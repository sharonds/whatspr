from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import structlog
from sqlmodel import Session

from .logging_config import configure_logging
from .middleware import RequestLogMiddleware
from .models import init_db, engine, SessionModel
from .config import settings
from .router import (
    get_or_create_session,
    save_answer,
    next_unanswered_field,
    answered_fields,
    record_message_sid,
)
from .security import ensure_twilio
from .prompts import question_for

configure_logging()
log = structlog.get_logger("main")

app = FastAPI(title="WhatsPR – Day‑1 stable")
app.add_middleware(RequestLogMiddleware)

RESET_WORDS = {"reset", "new", "start"}

@app.on_event("startup")
def _startup():
    init_db()
    log.info("db_ready")

def _plain(text: str):
    return PlainTextResponse(text)

def _force_new_session(phone: str) -> SessionModel:
    with Session(engine) as db:
        s = SessionModel(phone=phone)
        db.add(s); db.commit(); db.refresh(s)
        return s

@app.post("/whatsapp")
async def whatsapp(request: Request):
    await ensure_twilio(request)
    form = await request.form()
    phone = form.get("From", "")
    body = form.get("Body", "").strip()
    sid  = form.get("MessageSid", "")

    if not phone:
        return _plain("No phone.")

    # reset keyword
    if body.lower().split()[0] in RESET_WORDS:
        session = _force_new_session(phone)
        record_message_sid(session.id, sid)
        first_field = settings.required_fields[0]
        return _plain("Starting fresh – " + question_for(first_field))

    session = get_or_create_session(phone)

    # dedup
    if not record_message_sid(session.id, sid):
        return _plain("Duplicate ignored")

    # save answer for current field
    ans_count = len(answered_fields(session.id))
    if ans_count < len(settings.required_fields):
        field = settings.required_fields[ans_count]
        save_answer(session.id, field, body)
        log.info("saved", phone=phone[-4:], field=field)

    next_field = next_unanswered_field(session.id)
    if next_field:
        return _plain(question_for(next_field))
    else:
        # mark complete
        with Session(engine) as db:
            session.completed = True
            db.add(session); db.commit()
        return _plain("Great, that's everything. We'll draft your press release soon.")