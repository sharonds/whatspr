"""Thin wrapper around the OpenAI Assistants API.

Creates/re-uses threads, adds polling back-off loop, and surfaces
tool calls & assistant messages separately for conversation management.
"""

from __future__ import annotations

import os
import time
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from openai import OpenAI
from openai.types.beta import Thread, Assistant

log = logging.getLogger("whatspr.agent")

# ---------- one-time init ----------
# Lazy initialization to ensure env vars are loaded
_client = None


def get_client():
    """Get or create OpenAI client with proper API key."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            # Try loading from .env if not in environment
            from dotenv import load_dotenv

            load_dotenv()
            api_key = os.environ.get("OPENAI_API_KEY", "")
        _client = OpenAI(api_key=api_key)
    return _client


PROMPT = Path("prompts/assistant_v2.txt").read_text().strip()

# The assistant is created once; its ID is cached in a file so you don't
# recreate it every deploy (which would blow up #assistants quickly).
_ASSISTANT_CACHE = Path(".assistant_id")
_ASSISTANT_STAGING_CACHE = Path(".assistant_id.staging")


ATOMIC_FUNCS = [
    "save_announcement_type",
    "save_headline",
    "save_key_facts",
    "save_quotes",
    "save_boilerplate",
    "save_media_contact",
]


def _get_or_create_assistant() -> str:
    """Get or create OpenAI Assistant instance.

    Attempts to read assistant ID from staging cache first, then falls back to
    regular cache. If no cached ID exists, creates a new assistant with configured
    tools and saves the ID to cache.

    Returns:
        str: The OpenAI Assistant ID.

    Raises:
        Exception: If assistant creation fails.
    """
    # First, try to read from .assistant_id.staging
    try:
        if _ASSISTANT_STAGING_CACHE.exists():
            assistant_id = _ASSISTANT_STAGING_CACHE.read_text().strip()
            if assistant_id:
                log.info(
                    f"Using staging assistant ID from {_ASSISTANT_STAGING_CACHE}: {assistant_id}"
                )
                return assistant_id
    except Exception as e:
        log.warning(f"Failed to read staging assistant ID: {e}")

    # Fall back to regular .assistant_id
    if _ASSISTANT_CACHE.exists():
        return _ASSISTANT_CACHE.read_text().strip()

    assistant: Assistant = get_client().beta.assistants.create(
        name="WhatsPR Agent",
        instructions=PROMPT,
        model="gpt-4o-mini",  # Fastest and most cost-effective model
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
            *[
                {
                    "type": "function",
                    "function": {
                        "name": fn,
                        "parameters": {
                            "type": "object",
                            "properties": {"value": {"type": "string"}},
                            "required": ["value"],
                        },
                    },
                }
                for fn in ATOMIC_FUNCS
            ],
        ],
    )
    _ASSISTANT_CACHE.write_text(assistant.id)
    return assistant.id


ASSISTANT_ID = _get_or_create_assistant()

# ---------- helper API ----------


def create_thread() -> str:
    """Create a new OpenAI thread for conversation tracking.

    Returns:
        str: The unique thread ID for the created conversation thread.

    Raises:
        Exception: If thread creation fails due to API issues.
    """
    thread: Thread = get_client().beta.threads.create()
    return thread.id


def run_thread(thread_id: Optional[str], user_msg: str) -> Tuple[str, str, List[Dict[str, Any]]]:
    """Execute conversation turn with OpenAI Assistant.

    Sends user message to assistant, handles tool calls, and returns response.
    Creates new thread lazily if none provided. Implements exponential backoff
    polling for run completion with timeout protection.

    Args:
        thread_id: Optional conversation thread ID. Creates new if None.
        user_msg: User's message content to send to assistant.

    Returns:
        Tuple containing:
            - Assistant's reply text
            - Thread ID (created if was None)
            - List of tool call data (currently empty)

    Raises:
        RuntimeError: If run fails, is cancelled, or times out after max attempts.
        Exception: If API calls fail due to network or authentication issues.
    """
    from .validator_tool import validate_local

    # Lazy thread creation - only create when actually needed
    if thread_id is None:
        thread_id = create_thread()

    # 1. append user message
    get_client().beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_msg,
    )

    # 2. kick off a run
    run = get_client().beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        # No instructions override: already baked into the assistant.
        timeout=10,  # server-side request timeout
    )

    # 3. poll with exponential back-off and handle tool calls
    delay = 0.5
    max_attempts = 20  # Prevent infinite loops
    attempts = 0
    tool_calls_made = []  # Track tool calls for return value

    while attempts < max_attempts:
        attempts += 1
        run = get_client().beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == "completed":
            break
        elif run.status in {"failed", "cancelled"}:
            raise RuntimeError(f"Run {run.id} {run.status}: {run.last_error}")
        elif run.status == "requires_action" and run.required_action:
            # Handle tool calls
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                # Track this tool call for return value
                tool_calls_made.append(
                    {
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments),
                        "id": tool_call.id,
                    }
                )

                if tool_call.function.name == "validate_local":
                    args = json.loads(tool_call.function.arguments)
                    result = validate_local(args["name"], args["value"])
                    tool_outputs.append(
                        {"tool_call_id": tool_call.id, "output": json.dumps(result)}
                    )
                elif tool_call.function.name == "save_slot":
                    # Handle save_slot if needed
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"status": "saved"}),
                        }
                    )
                elif tool_call.function.name == "get_slot":
                    # Handle get_slot if needed
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"value": ""}),
                        }
                    )
                elif tool_call.function.name == "finish":
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"status": "finished"}),
                        }
                    )
                elif tool_call.function.name in ATOMIC_FUNCS:
                    # Handle atomic tools - return success for now
                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"status": "saved"}),
                        }
                    )

            # Submit tool outputs
            if tool_outputs:
                run = get_client().beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )
        else:
            # Still running, wait and try again
            time.sleep(delay)
            delay = min(delay * 2, 4)

    if attempts >= max_attempts:
        raise RuntimeError(f"Run {run.id} timed out after {max_attempts} attempts")

    # 4. fetch last assistant message (sorted by created_at desc)
    msgs = get_client().beta.threads.messages.list(thread_id=thread_id, limit=5)
    assistant_msg = next((m for m in msgs.data if m.role == "assistant"), None)
    reply_text = (
        assistant_msg.content[0].text.value
        if assistant_msg and hasattr(assistant_msg.content[0], "text")
        else "[No response]"
    )

    # 5. collect tool call payloads (if any) - return the actual calls made
    # Tool handling is done internally in the polling loop above
    tools: List[Dict[str, Any]] = tool_calls_made

    return reply_text, thread_id, tools
