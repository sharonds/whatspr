import time
from collections import defaultdict

WINDOW = 3  # seconds
_buffer: dict[str, tuple[str, float]] = defaultdict(lambda: ("", 0.0))


def aggregate(sender: str, msg: str) -> str | None:
    text, timestamp = _buffer[sender]
    now = time.time()
    if now - timestamp < WINDOW:
        _buffer[sender] = (text + " " + msg, now)
        return None  # still accumulating
    else:
        _buffer[sender] = (msg, now)
        return text.strip() if text else msg
