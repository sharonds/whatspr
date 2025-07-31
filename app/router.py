from typing import Optional, List
from sqlmodel import Session, select
from .models import engine, SessionModel, Answer, Message
from .config import settings
from .llm import rephrase_question

def get_or_create_session(phone: str) -> SessionModel:
    with Session(engine) as db:
        stmt = select(SessionModel).where(
            SessionModel.phone == phone, SessionModel.completed == False
        )
        existing = db.exec(stmt).first()
        if existing:
            return existing
        new = SessionModel(phone=phone)
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

def save_answer(session_id: int, field: str, value: str):
    with Session(engine) as db:
        ans = Answer(session_id=session_id, field=field, value=value)
        db.add(ans)
        db.commit()

def answered_fields(session_id: int) -> List[str]:
    with Session(engine) as db:
        return [
            row.field
            for row in db.exec(
                select(Answer.field).where(Answer.session_id == session_id)
            ).all()
        ]

def next_unanswered_field(session_id: int) -> Optional[str]:
    answered = set(answered_fields(session_id))
    for f in settings.required_fields:
        if f not in answered:
            return f
    return None

def record_message_sid(session_id: int, sid: str) -> bool:
    """Return False if sid already exists (duplicate)."""
    with Session(engine) as db:
        if db.get(Message, sid):
            return False
        db.add(Message(id=sid, session_id=session_id))
        db.commit()
        return True