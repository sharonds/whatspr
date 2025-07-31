from fastapi import APIRouter, Request
from fastapi.responses import Response
from .agent import create_thread, run_thread
from .prefilter import clean_message, twiml
import structlog

router = APIRouter()
log = structlog.get_logger("agent")

_sessions: dict[str, str] = {}  # phone -> thread_id


@router.post("/agent")
async def agent_hook(request: Request):
    form = await request.form()
    phone = form.get("From", "")
    body = form.get("Body", "")
    clean = clean_message(body)
    if clean is None:
        return twiml("Please send text.")
    thread_id = _sessions.get(phone)
    if not thread_id:
        thread_id = create_thread().id
        _sessions[phone] = thread_id
    try:
        reply = run_thread(thread_id, clean)
    except Exception as e:
        log.error("agent_error", error=str(e))
        return twiml("Oops, temporary error. Try again.")
    return twiml(reply)
