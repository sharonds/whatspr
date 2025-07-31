from app.router import next_unanswered_field, answered_fields
from app.models import init_db, engine, SessionModel, Answer
from sqlmodel import Session

def test_next_field():
    init_db()
    with Session(engine) as db:
        s = SessionModel(phone="+100")
        db.add(s)
        db.commit()
        db.refresh(s)
        assert next_unanswered_field(s.id) == "announcement_type"
        db.add(Answer(session_id=s.id, field="announcement_type", value="funding"))
        db.commit()
        assert next_unanswered_field(s.id) == "headline"