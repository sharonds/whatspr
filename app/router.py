from typing import Optional, List
from sqlmodel import Session, select
from .models import engine, SessionModel, Answer
from .config import settings

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
            row
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