from app.router import get_or_create_session
from app.models import init_db, engine
from sqlmodel import Session
from app.main import is_reset

def test_is_reset_variants():
    assert is_reset('RESET')
    assert is_reset('reset 👍')
    assert is_reset('New')
    assert not is_reset('hello')
