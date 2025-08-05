"""Idle detection utilities for session management.

Provides functions to determine if a user session should be considered
idle based on last activity timestamps.
"""

from datetime import datetime, timedelta

IDLE_THRESHOLD = timedelta(hours=1)


def is_idle(last_seen: datetime) -> bool:
    """Check if enough time has passed since last seen.

    Args:
        last_seen: Timestamp of last user activity.

    Returns:
        bool: True if session is considered idle (>1 hour), False otherwise.
    """
    return datetime.utcnow() - last_seen > IDLE_THRESHOLD
