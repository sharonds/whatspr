"""WhatsApp webhook endpoints for AI agent conversation handling.

Provides FastAPI routes for processing WhatsApp messages through AI agent,
managing conversation sessions, and dispatching tool calls.
"""

from fastapi import APIRouter, Request
from .agent_runtime import run_thread, ATOMIC_FUNCS
from .prefilter import clean_message, twiml
from .validator_tool import validate_local
from . import tools_atomic as tools
import structlog
from typing import Dict, Optional

router = APIRouter()
log = structlog.get_logger("agent")

_sessions: Dict[str, Optional[str]] = {}  # phone -> thread_id (None until first message)


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
        log.info(
            "debug_request",
            phone_hash=phone[-4:] if phone else "none",
            body_length=len(clean),
        )
        reply, thread_id, tool_calls = run_thread(thread_id, clean)
        _sessions[phone] = thread_id  # Update session with actual thread_id
        log.info("debug_response", reply_length=len(reply), tool_count=len(tool_calls))

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
