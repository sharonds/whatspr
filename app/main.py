from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import logging
from sqlmodel import Session

from .logging_config import configure_logging
from .models import init_db, engine
from .router import (
    get_or_create_session,
    save_answer,
    next_unanswered_field,
    answered_fields,
    record_message_sid,
)
from .security import ensure_valid_twilio
from .llm import rephrase_question
from .config import settings

configure_logging()
log = logging.getLogger("whatspr")

app = FastAPI(title="WhatsPR MVP – Fix reset & better logging")

@app.on_event("startup")
def _startup():
    init_db()
    log.info("DB initialised")

def _plain(text: str) -> PlainTextResponse:
    return PlainTextResponse(text)

# --- helper functions -------------------------------------------------

from .models import SessionModel

RESET_KEYWORDS = {"reset", "new", "start"}

def is_reset(text: str) -> bool:
    clean = (
        text.encode("ascii", "ignore")
            .decode()
            .lower()
            .strip()
            .split()[0]  # take first word only
    )
    return clean in RESET_KEYWORDS

def force_new_session(phone: str) -> SessionModel:
    with Session(engine) as db:
        new = SessionModel(phone=phone)
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

# ----------------------------------------------------------------------

@app.post("/whatsapp")
async def whatsapp_hook(request: Request):
    await ensure_valid_twilio(request)

    form = await request.form()
    sender = form.get("From", "")
    body = form.get("Body", "").strip()
    msg_sid = form.get("MessageSid")

    if not sender:
        return _plain("No sender.")

    # Debug log (PII‑safe)
    log.info(
        "incoming",
        sid=msg_sid,
        phone_last4=sender[-4:],
        body_preview=body[:40],
    )

    if is_reset(body):
        session = force_new_session(sender)
        record_message_sid(session.id, msg_sid)  # store to avoid duplicates later
        return _plain(
            "Starting fresh! " + rephrase_question(settings.required_fields[0])
        )

    session = get_or_create_session(sender)

    # Dedup AFTER reset keyword check
    if not record_message_sid(session.id, msg_sid):
        return _plain("Duplicate ignored.")

    already_answered = answered_fields(session.id)

    if len(already_answered) < len(settings.required_fields):
        field_being_answered = settings.required_fields[len(already_answered)]
        save_answer(session.id, field_being_answered, body)
        log.info("saved_answer", field=field_being_answered)

    next_field = next_unanswered_field(session.id)

    if next_field is None:
        with Session(engine) as db:
            session.completed = True
            db.add(session)
            db.commit()
        return _plain("Great, that's everything we need! We'll draft your press release shortly.")

    return _plain(rephrase_question(next_field))