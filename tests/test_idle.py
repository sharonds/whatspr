
from datetime import datetime, timedelta
from app.idle import is_idle
def test_idle():
    old = datetime.utcnow() - timedelta(hours=2)
    assert is_idle(old)
    recent = datetime.utcnow()
    assert not is_idle(recent)
