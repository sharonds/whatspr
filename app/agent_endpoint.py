"""WhatsApp webhook endpoints for AI agent conversation handling.

Provides FastAPI routes for processing WhatsApp messages through AI agent,
managing conversation sessions, and dispatching tool calls with timeout protection.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from fastapi import APIRouter, Request
from .agent_runtime import run_thread, ATOMIC_FUNCS
from .prefilter import clean_message, twiml
from .validator_tool import validate_local
from . import tools_atomic as tools
import structlog
from typing import Dict, Optional, Tuple, List

router = APIRouter()
log = structlog.get_logger("agent")

_sessions: Dict[str, Optional[str]] = {}  # phone -> thread_id (None until first message)

# Maximum time to spend on AI processing (Twilio timeout is ~15-20s)
MAX_AI_PROCESSING_TIME = 8.0  # Leave 7-12s buffer for request/response overhead


async def run_thread_with_timeout(thread_id: Optional[str], user_msg: str, timeout_seconds: float = MAX_AI_PROCESSING_TIME) -> Tuple[str, str, List[dict]]:
    """Run thread with timeout protection to prevent Twilio webhook timeouts.
    
    Args:
        thread_id: Optional thread ID for conversation continuation.
        user_msg: User message to process.
        timeout_seconds: Maximum time to wait for response.
        
    Returns:
        Tuple of (reply, thread_id, tool_calls) or fallback response on timeout.
    """
    start_time = time.time()
    
    try:
        # Run the blocking OpenAI call in a thread with asyncio timeout
        loop = asyncio.get_event_loop()
        task = loop.run_in_executor(None, run_thread, thread_id, user_msg)
        reply, thread_id, tool_calls = await asyncio.wait_for(task, timeout=timeout_seconds)
        
        elapsed = time.time() - start_time
        log.info("ai_processing_time", elapsed_seconds=elapsed, timeout_seconds=timeout_seconds)
        
        return reply, thread_id, tool_calls
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        log.warning("ai_timeout", elapsed_seconds=elapsed, timeout_seconds=timeout_seconds, user_msg=user_msg[:100])
        
        # Return a graceful fallback response
        fallback_reply = "I'm processing your request. Please give me a moment and try again shortly."
        return fallback_reply, thread_id or "", []
        
    except Exception as e:
        elapsed = time.time() - start_time
        log.error("ai_error_in_timeout", error=str(e), elapsed_seconds=elapsed, exc_info=True)
        
        # Return error fallback
        fallback_reply = "I'm having trouble processing your request right now. Please try again."
        return fallback_reply, thread_id or "", []


# Tool dispatch table for cleaner handling
def save_slot_fn(name: str, value: str) -> dict:
    """Save slot value with logging (placeholder implementation).

    Args:
        name: Slot name to save.
        value: Value to save for the slot.

    Returns:
        dict: Status response with saved slot information.
    """
    log.info("save_slot", name=name, value=value)
    return {"status": "saved", "name": name, "value": value}


def get_slot_fn(name: str) -> dict:
    """Retrieve slot value with logging (placeholder implementation).

    Args:
        name: Slot name to retrieve.

    Returns:
        dict: Slot information with empty value (placeholder).
    """
    log.info("get_slot", name=name)
    return {"value": "", "name": name}


def finish_fn() -> dict:
    """Mark conversation as finished with logging.

    Returns:
        dict: Completion status response.
    """
    log.info("finish")
    return {"status": "finished"}


TOOL_DISPATCH = {
    "save_slot": save_slot_fn,
    "get_slot": get_slot_fn,
    "validate_local": validate_local,
    "finish": finish_fn,
    **{fn: getattr(tools, fn) for fn in ATOMIC_FUNCS},
}


@router.post("/agent")
async def agent_hook(request: Request):
    """Main agent endpoint for processing WhatsApp messages.

    Handles incoming WhatsApp messages through AI agent conversation flow.
    Manages session state, processes reset commands, and executes tool calls.

    Args:
        request: FastAPI request containing WhatsApp webhook data.

    Returns:
        Response: TwiML response with agent's reply message.
    """
    form = await request.form()
    phone = str(form.get("From", ""))
    body = str(form.get("Body", ""))
    clean = clean_message(body)
    if clean is None:
        return twiml("Please send text.")

    # Handle reset commands
    if clean.lower() in ["reset", "restart", "start over", "menu", "start"]:
        log.info("session_reset", phone_hash=phone[-4:] if phone else "none")
        # Clear session, thread will be created lazily when needed
        _sessions[phone] = None
        return twiml(
            "👋 Hi! What kind of announcement?\n  Press 1 for Funding round\n  Press 2 for Product launch\n  Press 3 for Partnership / integration"
        )

    # Get thread_id (may be None for new sessions)
    thread_id = _sessions.get(phone)

    # Pre-process numeric menu selections
    if clean.strip() in ["1", "1️⃣"]:
        clean = "I want to announce a funding round"
    elif clean.strip() in ["2", "2️⃣"]:
        clean = "I want to announce a product launch"
    elif clean.strip() in ["3", "3️⃣"]:
        clean = "I want to announce a partnership or integration"

    try:
        request_start_time = time.time()
        log.info(
            "debug_request",
            phone_hash=phone[-4:] if phone else "none",
            body_length=len(clean),
        )
        
        # Use timeout-protected AI processing
        reply, thread_id, tool_calls = await run_thread_with_timeout(thread_id, clean)
        _sessions[phone] = thread_id  # Update session with actual thread_id
        
        processing_time = time.time() - request_start_time
        log.info("debug_response", reply_length=len(reply), tool_count=len(tool_calls), total_time=processing_time)

        # Handle tool calls using dispatch table
        for call in tool_calls:
            call_dict = dict(call)  # Ensure proper dict type for type checker
            if call_dict.get("name") in TOOL_DISPATCH:
                TOOL_DISPATCH[call_dict["name"]](**call_dict.get("arguments", {}))
                log.info("tool_executed", name=call_dict["name"])
            else:
                log.warning("unknown_tool", name=call_dict.get("name", "unknown"))

    except Exception as e:
        log.error("agent_error", error=str(e), error_type=type(e).__name__, exc_info=True)
        return twiml("Oops, temporary error. Try again.")
    return twiml(reply)


@router.post("/whatsapp")
async def whatsapp_hook(request: Request):
    """Primary WhatsApp webhook endpoint for agent mode.

    Routes WhatsApp webhook requests to the agent conversation handler
    when agent mode is enabled as the default processing mode.

    Args:
        request: FastAPI request containing WhatsApp webhook data.

    Returns:
        Response: TwiML response from agent_hook.
    """
    return await agent_hook(request)
