from fastapi import APIRouter, Request
from fastapi.responses import Response
from .agent_runtime import create_thread, run_thread
from .prefilter import clean_message, twiml
from .validator_tool import validate_local
import structlog

router = APIRouter()
log = structlog.get_logger("agent")

_sessions: dict[str, str] = {}  # phone -> thread_id


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
        thread_id = create_thread()  # Fixed: create_thread() already returns str
        _sessions[phone] = thread_id
    try:
        reply, tools = run_thread(thread_id, clean)  # Now returns both reply and tools
        
        # Handle tool calls if any
        for tool in tools:
            if tool["name"] == "validate_local":
                args = tool["arguments"]
                result = validate_local(args["name"], args["value"])
                log.info("validation_result", name=args["name"], value=args["value"], result=result)
            # Add other tool handlers as needed
        
    except Exception as e:
        log.error("agent_error", error=str(e))
        return twiml("Oops, temporary error. Try again.")
    return twiml(reply)


@router.post("/whatsapp")
async def whatsapp_hook(request: Request):
    """Main WhatsApp endpoint when agent is default"""
    return await agent_hook(request)
