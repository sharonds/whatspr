from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import logging

from .logging_config import configure_logging
from .models import init_db
from .router import (
    get_or_create_session,
    save_answer,
    next_unanswered_field,
    answered_fields,
    close_session,
)
from .prompts import question_for
from .config import settings

configure_logging()
log = logging.getLogger("whatspr")

app = FastAPI(title="WhatsPR MVP")

@app.on_event("startup")
def _startup():
    init_db()
    log.info("DB initialised")

def _plain(text: str) -> PlainTextResponse:
    return PlainTextResponse(text)

def is_reset_command(body: str) -> bool:
    """Check if the message is a reset command."""
    return body.lower().strip() in ["reset", "restart", "start over"]

@app.post("/whatsapp")
async def whatsapp_hook(request: Request):
    form = await request.form()
    sender = str(form.get("From", ""))
    body = str(form.get("Body", "")).strip()
    log.info(f"incoming from {sender}: {body}")

    if not sender:
        return _plain("No sender.")

    # Handle reset command
    if is_reset_command(body):
        close_session(sender)
        log.info(f"Reset session for {sender}")
        return _plain("Session reset! Let's start fresh. What's the name of your company?")

    session = get_or_create_session(sender)
    
    if session.id is None:
        log.error(f"Session creation failed for {sender}")
        return _plain("Sorry, there was an error. Please try again.")
    
    already_answered = answered_fields(session.id)

    # Save body as answer to current question if we haven't captured it yet
    if len(already_answered) < len(settings.required_fields):
        field_being_answered = settings.required_fields[len(already_answered)]
        save_answer(session.id, field_being_answered, body)
        log.info(f"saved_answer field={field_being_answered}")

    # Ask next question or finish
    next_field = next_unanswered_field(session.id)
    if next_field:
        return _plain(question_for(next_field))
    else:
        return _plain(
            "Great, that's everything we need! We'll draft your press release shortly."
        )