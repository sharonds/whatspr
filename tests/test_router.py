from app.router import next_unanswered_field, answered_fields, get_or_create_session, save_answer
from app.models import init_db, engine
from sqlmodel import Session
def test_flow():
    init_db()
    phone = "+100"
    s = get_or_create_session(phone)
    assert next_unanswered_field(s.id) == "announcement_type"
    save_answer(s.id, "announcement_type", "funding")
    assert next_unanswered_field(s.id) == "headline"