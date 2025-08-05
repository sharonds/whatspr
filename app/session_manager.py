"""Session management with TTL-based cleanup.

Provides SessionManager for managing conversation sessions with automatic cleanup
to prevent memory leaks in the WhatsApp chatbot.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass

from .session_config.session_config import SessionConfig

log = logging.getLogger("whatspr.session")


@dataclass
class SessionEntry:
    """Individual session entry with timestamp.

    Args:
        thread_id: OpenAI thread ID for the conversation.
        created_at: When the session was created.
        last_accessed: When the session was last accessed.
    """

    thread_id: str
    created_at: datetime
    last_accessed: datetime


class SessionManager:
    """Manages conversation sessions with TTL-based cleanup.

    Provides automatic cleanup of expired sessions to prevent memory leaks.
    Thread-safe for concurrent access from multiple requests.

    Args:
        config: Session configuration including TTL and cleanup intervals.
    """

    def __init__(self, config: Optional[SessionConfig] = None):
        """Initialize SessionManager with configuration.

        Args:
            config: Session configuration. Uses defaults if None.
        """
        self.config = config or SessionConfig()
        self._sessions: Dict[str, SessionEntry] = {}
        self._last_cleanup = datetime.now()

        # Metrics tracking
        self._total_sessions_created = 0
        self._total_sessions_expired = 0

        log.info(
            "session_manager_initialized",
            ttl_seconds=self.config.ttl_seconds,
            cleanup_interval=self.config.cleanup_interval,
        )

    def get_session(self, phone: str) -> Optional[str]:
        """Get session thread_id for phone number.

        Automatically triggers cleanup if interval has passed.
        Returns None if session doesn't exist or has expired.

        Args:
            phone: Phone number to look up session for.

        Returns:
            Optional[str]: Thread ID if session exists and is valid, None otherwise.
        """
        # Check if cleanup is needed
        self._maybe_cleanup()

        entry = self._sessions.get(phone)
        if entry is None:
            return None

        # Check if session has expired
        if self._is_expired(entry):
            self._remove_session_entry(phone)
            return None

        # Update last accessed time
        entry.last_accessed = datetime.now()
        return entry.thread_id

    def set_session(self, phone: str, thread_id: str) -> None:
        """Set session thread_id for phone number.

        Creates new session or updates existing one.

        Args:
            phone: Phone number to set session for.
            thread_id: OpenAI thread ID to associate with phone.
        """
        now = datetime.now()

        if phone not in self._sessions:
            self._total_sessions_created += 1

        self._sessions[phone] = SessionEntry(thread_id=thread_id, created_at=now, last_accessed=now)

        log.debug("session_set", phone_hash=phone[-4:], thread_id=thread_id[:20])

    def remove_session(self, phone: str) -> bool:
        """Remove session for phone number.

        Args:
            phone: Phone number to remove session for.

        Returns:
            bool: True if session was removed, False if it didn't exist.
        """
        return self._remove_session_entry(phone)

    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions.

        Returns:
            int: Number of sessions removed.
        """
        now = datetime.now()
        expired_phones = []

        for phone, entry in self._sessions.items():
            if self._is_expired(entry):
                expired_phones.append(phone)

        # Remove expired sessions
        for phone in expired_phones:
            self._remove_session_entry(phone)

        self._total_sessions_expired += len(expired_phones)
        self._last_cleanup = now

        if expired_phones:
            log.info(
                "session_cleanup_completed",
                removed_count=len(expired_phones),
                remaining_count=len(self._sessions),
            )

        return len(expired_phones)

    def get_session_count(self) -> int:
        """Get current number of active sessions.

        Returns:
            int: Number of active sessions.
        """
        return len(self._sessions)

    def estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes.

        Provides rough estimate for monitoring purposes.

        Returns:
            int: Estimated memory usage in bytes.
        """
        if not self._sessions:
            return 0

        # Estimate average sizes
        avg_phone_size = 15  # "+1234567890" format
        avg_thread_size = 30  # "thread_" + UUID format
        entry_overhead = 100  # datetime objects and dict overhead

        total_size = len(self._sessions) * (avg_phone_size + avg_thread_size + entry_overhead)
        return total_size

    def get_metrics(self) -> Dict[str, Any]:
        """Get session management metrics.

        Returns:
            Dict[str, Any]: Metrics including counts and memory usage.
        """
        return {
            'active_sessions': len(self._sessions),
            'total_sessions_created': self._total_sessions_created,
            'total_sessions_expired': self._total_sessions_expired,
            'estimated_memory_bytes': self.estimate_memory_usage(),
            'last_cleanup': self._last_cleanup.isoformat(),
            'config': {
                'ttl_seconds': self.config.ttl_seconds,
                'cleanup_interval': self.config.cleanup_interval,
            },
        }

    def migrate_from_dict(self, sessions_dict: Dict[str, Optional[str]]) -> int:
        """Migrate from existing _sessions dictionary.

        Args:
            sessions_dict: Existing sessions dictionary (phone -> thread_id).

        Returns:
            int: Number of sessions migrated.
        """
        migrated_count = 0
        now = datetime.now()

        for phone, thread_id in sessions_dict.items():
            if thread_id and thread_id.strip():  # Only migrate valid thread_ids
                self._sessions[phone] = SessionEntry(
                    thread_id=thread_id, created_at=now, last_accessed=now
                )
                migrated_count += 1

        self._total_sessions_created += migrated_count

        log.info(
            "sessions_migrated",
            migrated_count=migrated_count,
            skipped_count=len(sessions_dict) - migrated_count,
        )

        return migrated_count

    def _is_expired(self, entry: SessionEntry) -> bool:
        """Check if session entry has expired.

        Args:
            entry: Session entry to check.

        Returns:
            bool: True if session has expired.
        """
        age = datetime.now() - entry.last_accessed
        return age.total_seconds() > self.config.ttl_seconds

    def _remove_session_entry(self, phone: str) -> bool:
        """Remove session entry from internal storage.

        Args:
            phone: Phone number to remove.

        Returns:
            bool: True if entry was removed, False if it didn't exist.
        """
        if phone in self._sessions:
            del self._sessions[phone]
            log.debug("session_removed", phone_hash=phone[-4:])
            return True
        return False

    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed since last cleanup."""
        time_since_cleanup = datetime.now() - self._last_cleanup
        if time_since_cleanup.total_seconds() >= self.config.cleanup_interval:
            self.cleanup_expired_sessions()
