"""Message aggregation utilities for handling rapid message sequences.

Provides buffering functionality to combine multiple messages from the same
sender within a time window to handle rapid typing or message splitting.
"""

import time
from collections import defaultdict

WINDOW = 3  # seconds
_buffer: dict[str, tuple[str, float]] = defaultdict(lambda: ("", 0.0))


def aggregate(sender: str, msg: str) -> str | None:
    """Aggregate messages from sender within time window.

    Args:
        sender: Message sender identifier.
        msg: New message content to aggregate.

    Returns:
        Optional[str]: Combined message if window expired, None if still buffering.
    """
    text, timestamp = _buffer[sender]
    now = time.time()
    if now - timestamp < WINDOW:
        _buffer[sender] = (text + " " + msg, now)
        return None  # still accumulating
    else:
        _buffer[sender] = (msg, now)
        return text.strip() if text else msg
