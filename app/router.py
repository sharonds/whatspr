from typing import List, Optional
from sqlmodel import Session, select
from .models import engine, SessionModel, Answer, Message
from .config import settings

def get_or_create_session(phone: str) -> SessionModel:
    with Session(engine) as db:
        stmt = select(SessionModel).where(
            SessionModel.phone == phone, SessionModel.completed == False
        )
        session = db.exec(stmt).first()
        if session:
            return session
        new = SessionModel(phone=phone)
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

def answered_fields(session_id: int) -> List[str]:
    with Session(engine) as db:
        return [r for r in db.exec(
            select(Answer.field).where(Answer.session_id == session_id)
        ).all()]

def save_answer(session_id: int, field: str, value: str):
    with Session(engine) as db:
        db.add(Answer(session_id=session_id, field=field, value=value))
        db.commit()

def next_unanswered_field(session_id: int) -> Optional[str]:
    answered = set(answered_fields(session_id))
    for f in settings.required_fields:
        if f not in answered:
            return f
    return None

def record_message_sid(session_id: int, sid: str) -> bool:
    with Session(engine) as db:
        if db.get(Message, sid):
            return False
        db.add(Message(id=sid, session_id=session_id))
        db.commit()
        return True