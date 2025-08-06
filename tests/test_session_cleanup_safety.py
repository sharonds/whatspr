"""Session Cleanup Safety Testing.

Tests that cleanup operations never interfere with active conversations
or cause data loss during message processing.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta

from app.session_manager import SessionManager, SessionEntry
from app.session_config.session_config import SessionConfig
from tests.utils.rate_limiter import RateLimitedTestCase


class TestSessionCleanupSafety(RateLimitedTestCase):
    """Test session cleanup safety during active operations."""

    def setup_method(self, method):
        """Set up test with custom configuration for cleanup testing."""
        super().setup_method(method)
        self.test_config = SessionConfig(
            ttl_seconds=2,  # Short TTL for testing
            cleanup_interval=0.5,  # Frequent cleanup
            allow_test_values=True
        )
        self.session_manager = SessionManager(self.test_config)

    def test_cleanup_preserves_active_sessions(self):
        """Test cleanup only removes expired sessions, preserves active ones."""
        active_phone = "active_user"
        expired_phone = "expired_user"

        active_thread = "thread_active"
        expired_thread = "thread_expired"

        # Create active session
        self.session_manager.set_session(active_phone, active_thread)

        # Create already-expired session by manipulating timestamps
        expired_time = datetime.now() - timedelta(seconds=5)
        self.session_manager._sessions[expired_phone] = SessionEntry(
            thread_id=expired_thread, created_at=expired_time, last_accessed=expired_time
        )

        # Verify both sessions exist
        assert len(self.session_manager._sessions) == 2
        assert self.session_manager.get_session(active_phone) == active_thread

        # Force cleanup
        removed_count = self.session_manager.cleanup_expired_sessions()

        # Verify only expired session removed
        assert removed_count == 1
        assert self.session_manager.get_session(active_phone) == active_thread
        assert self.session_manager.get_session(expired_phone) is None
        assert len(self.session_manager._sessions) == 1

    def test_concurrent_cleanup_and_access(self):
        """Test cleanup running while sessions are being accessed."""
        phone = "concurrent_user"
        thread_id = "thread_concurrent"

        # Create session
        self.session_manager.set_session(phone, thread_id)

        # Flag to control test execution
        keep_accessing = True
        access_results = []
        cleanup_results = []

        def continuous_access():
            """Continuously access session to keep it active."""
            while keep_accessing:
                result = self.session_manager.get_session(phone)
                access_results.append(result)
                time.sleep(0.1)

        def periodic_cleanup():
            """Periodically force cleanup."""
            cleanup_count = 0
            while keep_accessing and cleanup_count < 10:
                removed = self.session_manager.cleanup_expired_sessions()
                cleanup_results.append(removed)
                time.sleep(0.2)
                cleanup_count += 1

        # Start concurrent operations
        access_thread = threading.Thread(target=continuous_access)
        cleanup_thread = threading.Thread(target=periodic_cleanup)

        access_thread.start()
        cleanup_thread.start()

        # Let them run for 2 seconds
        time.sleep(2)
        keep_accessing = False

        # Wait for completion
        access_thread.join()
        cleanup_thread.join()

        # Verify session remained active throughout
        assert all(
            result == thread_id for result in access_results
        ), f"Session access failed during cleanup: {access_results}"

        # Verify final session state is correct
        final_result = self.session_manager.get_session(phone)
        assert final_result == thread_id

    def test_cleanup_during_session_creation(self):
        """Test cleanup doesn't interfere with new session creation."""
        users_count = 10
        creation_results = {}

        # Create expired sessions to trigger cleanup
        for i in range(5):
            expired_phone = f"expired_{i}"
            expired_time = datetime.now() - timedelta(seconds=5)
            self.session_manager._sessions[expired_phone] = SessionEntry(
                thread_id=f"expired_thread_{i}", created_at=expired_time, last_accessed=expired_time
            )

        def create_sessions_during_cleanup():
            """Create new sessions while cleanup is happening."""
            for i in range(users_count):
                phone = f"new_user_{i}"
                thread_id = f"new_thread_{i}"

                # Set session (this might trigger cleanup internally)
                self.session_manager.set_session(phone, thread_id)

                # Immediately verify session was created correctly
                retrieved = self.session_manager.get_session(phone)
                creation_results[phone] = {
                    'expected': thread_id,
                    'retrieved': retrieved,
                    'success': retrieved == thread_id,
                }

                # Small delay to interleave with cleanup
                time.sleep(0.05)

        # Create sessions concurrently with cleanup
        create_sessions_during_cleanup()

        # Verify all new sessions were created successfully
        assert len(creation_results) == users_count
        failed_creations = [
            phone for phone, result in creation_results.items() if not result['success']
        ]
        assert not failed_creations, f"Failed session creations: {failed_creations}"

        # Verify expired sessions were cleaned up
        final_session_count = len(self.session_manager._sessions)
        assert (
            final_session_count == users_count
        ), f"Expected {users_count} sessions, got {final_session_count}"

    def test_cleanup_thread_safety(self):
        """Test cleanup operations are thread-safe."""
        session_count = 20
        cleanup_threads = 3

        # Create mix of active and expired sessions
        for i in range(session_count):
            phone = f"thread_safety_user_{i}"
            thread_id = f"thread_{i}"

            if i % 3 == 0:  # Make every 3rd session expired
                expired_time = datetime.now() - timedelta(seconds=5)
                self.session_manager._sessions[phone] = SessionEntry(
                    thread_id=thread_id, created_at=expired_time, last_accessed=expired_time
                )
            else:
                self.session_manager.set_session(phone, thread_id)

        # Count initial state
        initial_count = len(self.session_manager._sessions)
        expected_expired = session_count // 3 + (1 if session_count % 3 > 0 else 0)

        cleanup_results = []

        def run_cleanup():
            """Run cleanup and record results."""
            removed = self.session_manager.cleanup_expired_sessions()
            cleanup_results.append(removed)

        # Run multiple cleanup threads simultaneously
        threads = []
        for _ in range(cleanup_threads):
            thread = threading.Thread(target=run_cleanup)
            threads.append(thread)
            thread.start()

        # Wait for all cleanup operations
        for thread in threads:
            thread.join()

        # Verify cleanup results
        total_removed = sum(cleanup_results)
        final_count = len(self.session_manager._sessions)

        # Should have removed expected expired sessions (some cleanups might find 0)
        assert (
            total_removed <= expected_expired
        ), f"Over-cleaned: removed {total_removed}, expected max {expected_expired}"

        # Final count should be consistent
        expected_final = initial_count - total_removed
        assert (
            final_count == expected_final
        ), f"Inconsistent final count: {final_count}, expected {expected_final}"

    def test_cleanup_data_integrity(self):
        """Test cleanup preserves data integrity of remaining sessions."""
        phone1 = "integrity_user_1"
        phone2 = "integrity_user_2"
        phone3 = "integrity_user_3"

        thread1 = "thread_integrity_1"
        thread2 = "thread_integrity_2"
        thread3 = "thread_integrity_3"

        # Create sessions with different ages
        self.session_manager.set_session(phone1, thread1)
        time.sleep(0.5)
        self.session_manager.set_session(phone2, thread2)

        # Create expired session
        expired_time = datetime.now() - timedelta(seconds=5)
        self.session_manager._sessions[phone3] = SessionEntry(
            thread_id=thread3, created_at=expired_time, last_accessed=expired_time
        )

        # Capture original session data for active sessions
        original_entry1 = self.session_manager._sessions[phone1]
        original_entry2 = self.session_manager._sessions[phone2]

        # Run cleanup
        removed_count = self.session_manager.cleanup_expired_sessions()
        assert removed_count == 1

        # Verify remaining sessions have intact data
        remaining_entry1 = self.session_manager._sessions[phone1]
        remaining_entry2 = self.session_manager._sessions[phone2]

        # Thread IDs should be unchanged
        assert remaining_entry1.thread_id == original_entry1.thread_id
        assert remaining_entry2.thread_id == original_entry2.thread_id

        # Timestamps should be preserved (created_at unchanged, last_accessed might update)
        assert remaining_entry1.created_at == original_entry1.created_at
        assert remaining_entry2.created_at == original_entry2.created_at

        # Sessions should still function correctly
        assert self.session_manager.get_session(phone1) == thread1
        assert self.session_manager.get_session(phone2) == thread2
        assert self.session_manager.get_session(phone3) is None

    def test_cleanup_during_high_activity(self):
        """Test cleanup safety during high activity periods."""
        active_users = 15
        message_frequency = 0.1  # Messages every 100ms
        test_duration = 2  # 2 seconds

        # Create active users
        users = []
        for i in range(active_users):
            phone = f"high_activity_user_{i}"
            thread_id = f"thread_activity_{i}"
            self.session_manager.set_session(phone, thread_id)
            users.append((phone, thread_id))

        # Add some expired sessions to cleanup
        for i in range(5):
            expired_phone = f"expired_high_activity_{i}"
            expired_time = datetime.now() - timedelta(seconds=5)
            self.session_manager._sessions[expired_phone] = SessionEntry(
                thread_id=f"expired_thread_{i}", created_at=expired_time, last_accessed=expired_time
            )

        activity_results = {phone: [] for phone, _ in users}
        keep_activity = True

        def simulate_high_activity():
            """Simulate high activity on all sessions."""
            while keep_activity:
                for phone, expected_thread in users:
                    result = self.session_manager.get_session(phone)
                    activity_results[phone].append(result == expected_thread)
                time.sleep(message_frequency)

        # Start high activity simulation
        activity_thread = threading.Thread(target=simulate_high_activity)
        activity_thread.start()

        # Let it run with periodic cleanups
        time.sleep(test_duration)
        keep_activity = False
        activity_thread.join()

        # Verify all active sessions remained stable during high activity
        for phone, results in activity_results.items():
            success_rate = sum(results) / len(results) if results else 0
            assert success_rate == 1.0, f"Session {phone} had {success_rate:.2%} success rate"

        # Verify expired sessions were cleaned up
        for i in range(5):
            expired_phone = f"expired_high_activity_{i}"
            assert self.session_manager.get_session(expired_phone) is None

    def test_cleanup_metrics_consistency(self):
        """Test cleanup maintains consistent metrics."""
        # Create sessions
        active_count = 8
        expired_count = 3

        for i in range(active_count):
            phone = f"metrics_active_{i}"
            self.session_manager.set_session(phone, f"thread_{i}")

        for i in range(expired_count):
            phone = f"metrics_expired_{i}"
            expired_time = datetime.now() - timedelta(seconds=5)
            self.session_manager._sessions[phone] = SessionEntry(
                thread_id=f"expired_thread_{i}", created_at=expired_time, last_accessed=expired_time
            )

        # Get initial metrics
        initial_metrics = self.session_manager.get_metrics()
        assert initial_metrics['active_sessions'] == active_count + expired_count

        # Run cleanup
        removed_count = self.session_manager.cleanup_expired_sessions()
        assert removed_count == expired_count

        # Verify metrics consistency after cleanup
        final_metrics = self.session_manager.get_metrics()
        assert final_metrics['active_sessions'] == active_count
        assert final_metrics['total_sessions_expired'] == removed_count

        # Memory usage should decrease
        assert final_metrics['estimated_memory_bytes'] < initial_metrics['estimated_memory_bytes']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
