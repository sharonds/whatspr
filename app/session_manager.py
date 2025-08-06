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
            f"session_manager_initialized ttl_seconds={self.config.ttl_seconds} cleanup_interval={self.config.cleanup_interval}"
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
            try:
                log.debug("session_not_found", phone_hash=phone[-4:] if phone else "unknown")
            except Exception:
                pass
            return None

        # Check if session has expired
        if self._is_expired(entry):
            log.info(
                "session_expired_on_access",
                phone_hash=phone[-4:] if phone else "unknown",
                thread_id_prefix=entry.thread_id[:10],
                age_minutes=round((datetime.now() - entry.last_accessed).total_seconds() / 60, 1),
            )
            self._remove_session_entry(phone)
            return None

        # Update last accessed time and log successful access
        old_last_accessed = entry.last_accessed
        entry.last_accessed = datetime.now()

        # Log session access with useful metrics for MVP monitoring
        session_age_minutes = round(
            (entry.last_accessed - entry.created_at).total_seconds() / 60, 1
        )
        time_since_last_access = round(
            (entry.last_accessed - old_last_accessed).total_seconds() / 60, 1
        )

        log.debug(
            "session_accessed",
            phone_hash=phone[-4:] if phone else "unknown",
            thread_id_prefix=entry.thread_id[:10],
            session_age_minutes=session_age_minutes,
            minutes_since_last_access=time_since_last_access,
            total_active_sessions=len(self._sessions),
        )

        return entry.thread_id

    def set_session(self, phone: str, thread_id: str) -> None:
        """Set session thread_id for phone number.

        Creates new session or updates existing one.

        Args:
            phone: Phone number to set session for.
            thread_id: OpenAI thread ID to associate with phone.
        """
        now = datetime.now()
        is_new_session = phone not in self._sessions

        if is_new_session:
            self._total_sessions_created += 1

        self._sessions[phone] = SessionEntry(thread_id=thread_id, created_at=now, last_accessed=now)

        # Enhanced logging for MVP user tracking
        if is_new_session:
            try:
                log.info(
                    "session_created",
                    phone_hash=phone[-4:] if phone else "unknown",
                    thread_id_prefix=thread_id[:10],
                    total_sessions_created=self._total_sessions_created,
                    current_active_sessions=len(self._sessions),
                )
            except Exception as log_error:
                print(f"Session logging error: {log_error}")
        else:
            try:
                log.info(
                    "session_updated",
                    phone_hash=phone[-4:] if phone else "unknown",
                    new_thread_id_prefix=thread_id[:10],
                    current_active_sessions=len(self._sessions),
                )
            except Exception as log_error:
                print(f"Session update logging error: {log_error}")

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
        cleanup_start = datetime.now()
        expired_phones = []
        expired_details = []

        for phone, entry in self._sessions.items():
            if self._is_expired(entry):
                expired_phones.append(phone)
                # Collect details for enhanced logging
                age_minutes = round((cleanup_start - entry.last_accessed).total_seconds() / 60, 1)
                expired_details.append(
                    {
                        'phone_hash': phone[-4:] if phone else "unknown",
                        'thread_id_prefix': entry.thread_id[:10],
                        'age_minutes': age_minutes,
                    }
                )

        # Remove expired sessions
        for phone in expired_phones:
            self._remove_session_entry(phone)

        self._total_sessions_expired += len(expired_phones)
        self._last_cleanup = cleanup_start
        cleanup_duration = (datetime.now() - cleanup_start).total_seconds()

        # Enhanced cleanup logging for MVP monitoring
        if expired_phones:
            log.info(
                "session_cleanup_completed",
                removed_count=len(expired_phones),
                remaining_count=len(self._sessions),
                cleanup_duration_ms=round(cleanup_duration * 1000, 1),
                total_expired_lifetime=self._total_sessions_expired,
                memory_estimate_bytes=self.estimate_memory_usage(),
            )

            # Log details of expired sessions for debugging
            if len(expired_details) <= 5:  # Only log details for small cleanups
                for detail in expired_details:
                    log.debug("session_expired_detail", **detail)
            else:
                # For large cleanups, log summary statistics
                avg_age = sum(d['age_minutes'] for d in expired_details) / len(expired_details)
                max_age = max(d['age_minutes'] for d in expired_details)
                log.debug(
                    "session_cleanup_summary",
                    expired_count=len(expired_details),
                    avg_age_minutes=round(avg_age, 1),
                    max_age_minutes=round(max_age, 1),
                )
        else:
            # Log even when no cleanup needed for monitoring heartbeat
            log.debug(
                "session_cleanup_no_action",
                active_sessions=len(self._sessions),
                cleanup_duration_ms=round(cleanup_duration * 1000, 1),
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
            try:
                log.debug("session_removed", phone_hash=phone[-4:])
            except Exception:
                pass
            return True
        return False

    def _maybe_cleanup(self) -> None:
        """Run cleanup if enough time has passed since last cleanup."""
        time_since_cleanup = datetime.now() - self._last_cleanup
        if time_since_cleanup.total_seconds() >= self.config.cleanup_interval:
            self.cleanup_expired_sessions()
