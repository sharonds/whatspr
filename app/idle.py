from datetime import datetime, timedelta

IDLE_THRESHOLD = timedelta(hours=1)


def is_idle(last_seen: datetime) -> bool:
    return datetime.utcnow() - last_seen > IDLE_THRESHOLD
