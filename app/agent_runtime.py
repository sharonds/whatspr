# app/agent_runtime.py
"""
Thin wrapper around the OpenAI Assistants API.
– Creates / re-uses threads
– Adds a small polling back-off loop
– Surfaces tool calls & assistant messages separately
"""

from __future__ import annotations

import os
import time
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional

from openai import OpenAI
from openai.types.beta import Thread, Assistant
from openai.types.beta.threads import Message

log = logging.getLogger("whatspr.agent")

# ---------- one-time init ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

PROMPT = Path("prompts/assistant.txt").read_text().strip()

# The assistant is created once; its ID is cached in a file so you don't
# recreate it every deploy (which would blow up #assistants quickly).
_ASSISTANT_CACHE = Path(".assistant_id")
_ASSISTANT_STAGING_CACHE = Path(".assistant_id.staging")


def _get_or_create_assistant() -> str:
    # First, try to read from .assistant_id.staging
    try:
        if _ASSISTANT_STAGING_CACHE.exists():
            assistant_id = _ASSISTANT_STAGING_CACHE.read_text().strip()
            if assistant_id:
                log.info(f"Using staging assistant ID from {_ASSISTANT_STAGING_CACHE}: {assistant_id}")
                return assistant_id
    except Exception as e:
        log.warning(f"Failed to read staging assistant ID: {e}")
    
    # Fall back to regular .assistant_id
    if _ASSISTANT_CACHE.exists():
        return _ASSISTANT_CACHE.read_text().strip()

    assistant: Assistant = client.beta.assistants.create(
        name="WhatsPR Agent",
        instructions=PROMPT,
        model="gpt-3.5-turbo",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "save_slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["name", "value"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_slot",
                    "parameters": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "finish",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {  # NEW
                    "name": "validate_local",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["name", "value"],
                    },
                },
            },
        ],
    )
    _ASSISTANT_CACHE.write_text(assistant.id)
    return assistant.id


ASSISTANT_ID = _get_or_create_assistant()

# ---------- helper API ----------


def create_thread() -> str:
    """Return *thread_id*"""
    thread: Thread = client.beta.threads.create()
    return thread.id


def run_thread(thread_id: Optional[str], user_msg: str) -> Tuple[str, str, List[Dict[str, Any]]]:
    """
    Send user message, return assistant reply text, thread_id, and list of tool calls.
    If thread_id is None, creates a new thread lazily.
    Raises on permanent API error; handles polling / back-off.
    """
    from .validator_tool import validate_local

    # Lazy thread creation - only create when actually needed
    if thread_id is None:
        thread_id = create_thread()

    # 1. append user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_msg,
    )

    # 2. kick off a run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        # No instructions override: already baked into the assistant.
        timeout=10,  # server-side request timeout
    )

    # 3. poll with exponential back-off and handle tool calls
    delay = 0.5
    max_attempts = 20  # Prevent infinite loops
    attempts = 0

    while attempts < max_attempts:
        attempts += 1
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == "completed":
            break
        elif run.status in {"failed", "cancelled"}:
            raise RuntimeError(f"Run {run.id} {run.status}: {run.last_error}")
        elif run.status == "requires_action" and run.required_action:
            # Handle tool calls
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "validate_local":
                    args = json.loads(tool_call.function.arguments)
                    result = validate_local(args["name"], args["value"])
                    tool_outputs.append(
                        {"tool_call_id": tool_call.id, "output": json.dumps(result)}
                    )
                elif tool_call.function.name == "save_slot":
                    # Handle save_slot if needed
                    tool_outputs.append(
                        {"tool_call_id": tool_call.id, "output": json.dumps({"status": "saved"})}
                    )
                elif tool_call.function.name == "get_slot":
                    # Handle get_slot if needed
                    tool_outputs.append(
                        {"tool_call_id": tool_call.id, "output": json.dumps({"value": ""})}
                    )
                elif tool_call.function.name == "finish":
                    tool_outputs.append(
                        {"tool_call_id": tool_call.id, "output": json.dumps({"status": "finished"})}
                    )

            # Submit tool outputs
            if tool_outputs:
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )
        else:
            # Still running, wait and try again
            time.sleep(delay)
            delay = min(delay * 2, 4)

    if attempts >= max_attempts:
        raise RuntimeError(f"Run {run.id} timed out after {max_attempts} attempts")

    # 4. fetch last assistant message (sorted by created_at desc)
    msgs = client.beta.threads.messages.list(thread_id=thread_id, limit=5)
    assistant_msg = next((m for m in msgs.data if m.role == "assistant"), None)
    reply_text = (
        assistant_msg.content[0].text.value
        if assistant_msg and hasattr(assistant_msg.content[0], 'text')
        else "[No response]"
    )

    # 5. collect tool call payloads (if any)
    tools: List[Dict[str, Any]] = []
    for m in msgs.data:
        if m.role == "tool":
            tools.append(
                {
                    "name": m.content[0].tool_call.name,
                    "arguments": json.loads(m.content[0].tool_call.arguments or "{}"),
                }
            )

    return reply_text, thread_id, tools
