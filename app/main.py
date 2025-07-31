from fastapi import FastAPI, Request
from fastapi.responses import Response
import structlog
from sqlmodel import Session

from twilio.twiml.messaging_response import MessagingResponse

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
from .llm import rephrase_question
from .commands import maybe_command
from .prefilter import clean_message

configure_logging()
log = structlog.get_logger("main")

app = FastAPI(title="WhatsPR – Day-1 + LLM flag")
app.add_middleware(RequestLogMiddleware)

RESET_WORDS = {"reset", "new", "start"}


def twiml(text: str) -> Response:
    resp = MessagingResponse()
    resp.message(text)
    return Response(str(resp), media_type="application/xml")


@app.on_event("startup")
def _startup():
    init_db()
    log.info("db_ready")


def _force_new_session(phone: str) -> SessionModel:
    with Session(engine) as db:
        s = SessionModel(phone=phone)
        db.add(s)
        db.commit()
        db.refresh(s)
        return s


@app.post("/whatsapp")
async def whatsapp(request: Request):
    await ensure_twilio(request)
    form = await request.form()
    phone = str(form.get("From", ""))
    raw_body = str(form.get("Body", ""))
    sid = str(form.get("MessageSid", ""))

    if not phone:
        return twiml("")

    # Clean and validate the message first
    body = clean_message(raw_body)
    if body is None:
        return twiml("")  # Ignore invalid messages

    # Check if it's a command first
    current_session = get_or_create_session(phone)
    next_field = next_unanswered_field(current_session.id) if current_session.id else None
    command_response = maybe_command(body, next_field)
    if command_response:
        return command_response

    # reset keyword (legacy support)
    if body.lower().split()[0] in RESET_WORDS:
        session = _force_new_session(phone)
        if session.id:
            record_message_sid(session.id, sid)

        # Show menu instead of going directly to questions
        return twiml("👋 Hi! Pick the kind of announcement:\n  1️⃣ Funding round\n  2️⃣ Product launch\n  3️⃣ Partnership / integration")

    session = get_or_create_session(phone)
    if not session.id:
        return twiml("Sorry, there was an error. Please try again.")

    # For completely new sessions, show the menu
    if len(answered_fields(session.id)) == 0 and body.lower().split()[0] not in RESET_WORDS:
        # This is a new user, show the menu
        return twiml("👋 Hi! Pick the kind of announcement:\n  1️⃣ Funding round\n  2️⃣ Product launch\n  3️⃣ Partnership / integration")

    # dedup
    if not record_message_sid(session.id, sid):
        return twiml("")

    # Check if this is category selection (menu)
    answered_count = len(answered_fields(session.id))
    if answered_count == 0:
        # This is the first message - handle category selection
        body_lower = body.lower()
        if body_lower in ["1", "fund", "funding", "raise"]:
            save_answer(session.id, "announcement_type", "Funding round")
            log.info("saved", phone=phone[-4:], field="announcement_type")
        elif body_lower in ["2", "product", "launch", "feature"]:
            save_answer(session.id, "announcement_type", "Product launch")
            log.info("saved", phone=phone[-4:], field="announcement_type")
        elif body_lower in ["3", "partner", "partnership", "integration"]:
            save_answer(session.id, "announcement_type", "Partnership / integration")
            log.info("saved", phone=phone[-4:], field="announcement_type")
        else:
            # Invalid selection, show menu again
            return twiml("Please choose:\n  1️⃣ Funding round\n  2️⃣ Product launch\n  3️⃣ Partnership / integration")
    else:
        # save answer for subsequent questions
        # Use flow spec if available, otherwise fall back to legacy required_fields
        if settings.flow and 'slots' in settings.flow:
            field_list = [slot['id'] for slot in settings.flow['slots']]
        else:
            field_list = settings.required_fields

        if answered_count < len(field_list):
            field = field_list[answered_count]
            save_answer(session.id, field, body)
            log.info("saved", phone=phone[-4:], field=field)

    next_field = next_unanswered_field(session.id)
    if next_field:
        return twiml(rephrase_question(next_field))
    else:
        with Session(engine) as db:
            session.completed = True
            db.add(session)
            db.commit()
        return twiml("✅ Got everything—expect your draft in 24 h. Reply /status anytime.")
