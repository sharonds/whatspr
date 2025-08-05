"""Session and conversation flow routing utilities.

Provides database operations for managing user sessions, tracking answers,
and controlling conversation flow progression through press release data collection.
"""

from typing import List, Optional
from sqlmodel import Session, select
from .models import engine, SessionModel, Answer, Message
from .config import settings


def get_or_create_session(phone: str) -> SessionModel:
    """Get existing active session or create new one for phone number.

    Args:
        phone: User's phone number in international format.

    Returns:
        SessionModel: Active session for the phone number.
    """
    with Session(engine) as db:
        stmt = select(SessionModel).where(SessionModel.phone == phone, not SessionModel.completed)
        session = db.exec(stmt).first()
        if session:
            return session
        new = SessionModel(phone=phone)
        db.add(new)
        db.commit()
        db.refresh(new)
        return new


def answered_fields(session_id: int) -> List[str]:
    """Get list of field names that have been answered in a session.

    Args:
        session_id: Database ID of the session to check.

    Returns:
        List[str]: Field names that have answers recorded.
    """
    with Session(engine) as db:
        return [
            r for r in db.exec(select(Answer.field).where(Answer.session_id == session_id)).all()
        ]


def save_answer(session_id: int, field: str, value: str):
    """Save user's answer for a specific field in the session.

    Args:
        session_id: Database ID of the session.
        field: Field name/identifier for the answer.
        value: User's response value to save.
    """
    with Session(engine) as db:
        db.add(Answer(session_id=session_id, field=field, value=value))
        db.commit()


def next_unanswered_field(session_id: int) -> Optional[str]:
    """Find the next field that needs to be answered in the session.

    Checks answered fields against the configured flow or required fields
    to determine what question should be asked next.

    Args:
        session_id: Database ID of the session to check.

    Returns:
        Optional[str]: Next field name to collect, or None if all complete.
    """
    answered = set(answered_fields(session_id))

    # Use flow spec if available, otherwise fall back to legacy required_fields
    if settings.flow and "slots" in settings.flow:
        field_list = [slot["id"] for slot in settings.flow["slots"]]
    else:
        field_list = settings.required_fields

    for f in field_list:
        if f not in answered:
            return f
    return None


def record_message_sid(session_id: int, sid: str) -> bool:
    """Record Twilio message ID to prevent duplicate processing.

    Args:
        session_id: Database ID of the session.
        sid: Twilio MessageSid to record.

    Returns:
        bool: True if message was newly recorded, False if already exists.
    """
    with Session(engine) as db:
        if db.get(Message, sid):
            return False
        db.add(Message(id=sid, session_id=session_id))
        db.commit()
        return True
