from app.router import next_unanswered_field, get_or_create_session, save_answer
from app.models import init_db, engine, Answer
from sqlmodel import Session, select


def test_flow():
    init_db()
    phone = "+100"

    # Clean up any existing test data - use ORM approach
    with Session(engine) as db:
        # Get existing session for this phone and delete its answers
        from app.models import SessionModel

        existing_session = db.exec(
            select(SessionModel).where(SessionModel.phone == phone)
        ).first()
        if existing_session:
            # Delete answers for this session
            answers = db.exec(
                select(Answer).where(Answer.session_id == existing_session.id)
            ).all()
            for answer in answers:
                db.delete(answer)
            # Delete the session
            db.delete(existing_session)
            db.commit()

    s = get_or_create_session(phone)
    assert next_unanswered_field(s.id) == "announcement_type"
    save_answer(s.id, "announcement_type", "funding")
    assert next_unanswered_field(s.id) == "headline"
