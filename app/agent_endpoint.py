from fastapi import APIRouter, Request
from fastapi.responses import Response
from .agent_runtime import create_thread, run_thread
from .prefilter import clean_message, twiml
from .validator_tool import validate_local
import structlog

router = APIRouter()
log = structlog.get_logger("agent")

_sessions: dict[str, str] = {}  # phone -> thread_id


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
    thread_id = _sessions.get(phone)
    if not thread_id:
        thread_id = create_thread()
        _sessions[phone] = thread_id
    try:
        reply, tool_calls = run_thread(thread_id, clean)

        # Handle tool calls using dispatch table
        for call in tool_calls:
            if call["name"] in TOOL_DISPATCH:
                result = TOOL_DISPATCH[call["name"]](**call["arguments"])
                log.info(
                    "tool_result", name=call["name"], arguments=call["arguments"], result=result
                )
            else:
                log.warning("unknown_tool", name=call["name"])

    except Exception as e:
        log.error("agent_error", error=str(e))
        return twiml("Oops, temporary error. Try again.")
    return twiml(reply)


@router.post("/whatsapp")
async def whatsapp_hook(request: Request):
    """Main WhatsApp endpoint when agent is default"""
    return await agent_hook(request)
