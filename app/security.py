from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from .config import settings
import structlog

log = structlog.get_logger("security")
validator = RequestValidator(settings.twilio_auth_token)

async def ensure_twilio(request: Request):
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    if not validator.validate(url, dict(form), signature):
        log.warning("bad_signature", url=url)
        raise HTTPException(status_code=403, detail="Invalid signature")