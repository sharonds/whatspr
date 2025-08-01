from fastapi import APIRouter, Request
from fastapi.responses import Response
from .agent_runtime import create_thread, run_thread
from .prefilter import clean_message, twiml
from .validator_tool import validate_local
import structlog
from typing import Dict, Optional, List, Any

router = APIRouter()
log = structlog.get_logger("agent")

_sessions: Dict[str, Optional[str]] = {}  # phone -> thread_id (None until first message)


# Tool dispatch table for cleaner handling
def save_slot_fn(name: str, value: str) -> dict:
    """Save a slot value (placeholder implementation)"""
    log.info("save_slot", name=name, value=value)
    return {"status": "saved", "name": name, "value": value}


def get_slot_fn(name: str) -> dict:
    """Get a slot value (placeholder implementation)"""
    log.info("get_slot", name=name)
    return {"value": "", "name": name}


def finish_fn() -> dict:
    """Finish the conversation (placeholder implementation)"""
    log.info("finish")
    return {"status": "finished"}


TOOL_DISPATCH = {
    "save_slot": save_slot_fn,
    "get_slot": get_slot_fn,
    "validate_local": validate_local,
    "finish": finish_fn,
}


@router.post("/agent")
async def agent_hook(request: Request):
    form = await request.form()
    phone = str(form.get("From", ""))
    body = str(form.get("Body", ""))
    clean = clean_message(body)
    if clean is None:
        return twiml("Please send text.")

    # Handle reset commands
    if clean.lower() in ["reset", "restart", "start over", "menu", "start"]:
        log.info("session_reset", phone_hash=phone[-4:] if phone else "none")
        if phone in _sessions:
            del _sessions[phone]
        # Don't create thread immediately - use lazy creation
        _sessions[phone] = None
        return twiml(
            "👋 Hi! Pick the kind of announcement:\n  1️⃣ Funding round\n  2️⃣ Product launch\n  3️⃣ Partnership / integration"
        )

    thread_id = _sessions.get(phone)
    if not thread_id:
        thread_id = create_thread()
        _sessions[phone] = thread_id
    try:
        log.info(
            "debug_request", phone_hash=phone[-4:] if phone else "none", body_length=len(clean)
        )
        reply, thread_id, tool_calls = run_thread(thread_id, clean)
        _sessions[phone] = thread_id  # Update session with actual thread_id
        log.info("debug_response", reply_length=len(reply), tool_count=len(tool_calls))

        # Handle tool calls using dispatch table
        for call in tool_calls:
            call_dict = dict(call)  # Ensure proper dict type for type checker
            if call_dict.get("name") in TOOL_DISPATCH:
                result = TOOL_DISPATCH[call_dict["name"]](**call_dict.get("arguments", {}))
                log.info("tool_executed", name=call_dict["name"])
            else:
                log.warning("unknown_tool", name=call_dict.get("name", "unknown"))

    except Exception as e:
        log.error("agent_error", error=str(e), error_type=type(e).__name__, exc_info=True)
        return twiml("Oops, temporary error. Try again.")
    return twiml(reply)


@router.post("/whatsapp")
async def whatsapp_hook(request: Request):
    """Main WhatsApp endpoint when agent is default"""
    return await agent_hook(request)
