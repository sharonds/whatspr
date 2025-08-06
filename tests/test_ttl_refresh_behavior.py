"""TTL Refresh Behavior Testing.

Tests that active conversations properly extend session lifetime,
ensuring users don't lose context during ongoing press release creation.
"""

import pytest
import time
from datetime import datetime

from app.session_manager import SessionManager
from app.session_config.session_config import SessionConfig
from tests.utils.rate_limiter import RateLimitedTestCase


class TestTTLRefreshBehavior(RateLimitedTestCase):
    """Test TTL refresh behavior during active conversations."""

    def setup_method(self, method):
        """Set up test with custom TTL for controlled testing."""
        super().setup_method(method)
        # Use 3 second TTL for fast testing
        self.test_config = SessionConfig(
            ttl_seconds=3,  # 3 seconds for quick testing
            cleanup_interval=1,  # 1 second cleanup interval
            allow_test_values=True
        )
        self.session_manager = SessionManager(self.test_config)

    def test_active_conversation_extends_ttl(self):
        """Test that accessing session during TTL period extends lifetime."""
        phone = "active_user"
        thread_id = "thread_active_refresh"

        # Create initial session
        self.session_manager.set_session(phone, thread_id)

        # Wait 2 seconds (less than 3-second TTL)
        time.sleep(2)

        # Access session - this should refresh last_accessed time
        retrieved1 = self.session_manager.get_session(phone)
        assert retrieved1 == thread_id
        refresh_time = datetime.now()

        # Wait another 2 seconds (total 4 seconds from initial creation)
        time.sleep(2)

        # Session should still be valid because last access was only 2 seconds ago
        retrieved2 = self.session_manager.get_session(phone)
        assert retrieved2 == thread_id, "Session should still be active after refresh"

        # Verify session entry was actually updated
        entry = self.session_manager._sessions.get(phone)
        assert entry is not None
        assert entry.last_accessed > entry.created_at

        # Time between refresh and now should be less than TTL
        time_since_refresh = datetime.now() - refresh_time
        assert time_since_refresh.total_seconds() < self.test_config.ttl_seconds

    def test_inactive_conversation_expires(self):
        """Test that inactive sessions expire after TTL."""
        phone = "inactive_user"
        thread_id = "thread_inactive"

        # Create session
        self.session_manager.set_session(phone, thread_id)

        # Verify session exists
        retrieved1 = self.session_manager.get_session(phone)
        assert retrieved1 == thread_id

        # Wait longer than TTL without accessing
        time.sleep(4)  # 4 seconds > 3 second TTL

        # Session should be expired
        retrieved2 = self.session_manager.get_session(phone)
        assert retrieved2 is None, "Session should have expired"

    def test_multiple_refreshes_extend_lifetime(self):
        """Test multiple accesses keep extending session lifetime."""
        phone = "multi_refresh_user"
        thread_id = "thread_multi_refresh"

        # Create session
        self.session_manager.set_session(phone, thread_id)
        start_time = datetime.now()

        # Access session multiple times, each extending lifetime
        for i in range(5):
            # Wait 2 seconds (less than 3-second TTL)
            time.sleep(2)

            # Access session to refresh
            retrieved = self.session_manager.get_session(phone)
            assert retrieved == thread_id, f"Session should be active at iteration {i}"

            # Verify we're still within extended lifetime
            elapsed = datetime.now() - start_time
            expected_max_lifetime = (i + 1) * 2 + self.test_config.ttl_seconds
            assert elapsed.total_seconds() < expected_max_lifetime

        # After 5 iterations × 2 seconds = 10 seconds total
        # Session should still be active due to continuous refreshing
        total_elapsed = datetime.now() - start_time
        assert total_elapsed.total_seconds() > self.test_config.ttl_seconds * 2
        assert self.session_manager.get_session(phone) == thread_id

    def test_ttl_refresh_during_realistic_conversation(self):
        """Test TTL refresh behavior during realistic press release conversation."""
        phone = "pr_conversation_user"
        thread_id = "thread_pr_conversation"

        # Use longer TTL for realistic conversation (30 seconds)
        realistic_config = SessionConfig(ttl_seconds=30, cleanup_interval=10, allow_test_values=True)
        realistic_manager = SessionManager(realistic_config)

        # Create session
        realistic_manager.set_session(phone, thread_id)
        conversation_start = datetime.now()

        # Simulate realistic conversation timing
        # Press release conversations typically have messages every 30-120 seconds
        conversation_steps = [
            ("What type of announcement?", 5),
            ("Let me gather key facts", 15),
            ("Need some quotes", 20),
            ("Company boilerplate?", 25),
            ("Media contact info", 10),
            ("Review and finalize", 30),
        ]

        for step_msg, delay_seconds in conversation_steps:
            # Wait realistic delay
            time.sleep(delay_seconds / 10)  # Shortened for testing

            # Access session (simulates processing user message)
            retrieved = realistic_manager.get_session(phone)
            assert retrieved == thread_id, f"Session lost during: {step_msg}"

            # Verify session is being refreshed
            entry = realistic_manager._sessions[phone]
            time_since_start = datetime.now() - conversation_start
            time_since_access = datetime.now() - entry.last_accessed

            # Last access should be very recent (< 1 second)
            assert time_since_access.total_seconds() < 1

            # But conversation might have been going on longer than TTL
            if time_since_start.total_seconds() > realistic_config.ttl_seconds:
                # Session should still be active due to refreshes
                assert retrieved is not None, "Long conversation should stay active with refreshes"

    def test_ttl_refresh_edge_cases(self):
        """Test edge cases in TTL refresh behavior."""
        # Test rapid successive accesses
        phone1 = "rapid_user"
        thread_id1 = "thread_rapid"

        self.session_manager.set_session(phone1, thread_id1)

        # Rapid accesses within same second
        for _ in range(10):
            retrieved = self.session_manager.get_session(phone1)
            assert retrieved == thread_id1
            time.sleep(0.1)

        # Test access right at expiration boundary
        phone2 = "boundary_user"
        thread_id2 = "thread_boundary"

        self.session_manager.set_session(phone2, thread_id2)

        # Wait almost to TTL limit
        time.sleep(2.9)  # Just under 3 second TTL

        # Access should still work and refresh
        retrieved = self.session_manager.get_session(phone2)
        assert retrieved == thread_id2

        # Now wait past original TTL
        time.sleep(2)  # Total would be 4.9 seconds from creation, but refreshed at 2.9

        # Should still be active due to refresh
        retrieved_after_original_ttl = self.session_manager.get_session(phone2)
        assert retrieved_after_original_ttl == thread_id2

    def test_ttl_refresh_with_cleanup_timing(self):
        """Test TTL refresh behavior when cleanup runs during conversation."""
        phone = "cleanup_timing_user"
        thread_id = "thread_cleanup_timing"

        # Short cleanup interval to force frequent cleanups
        cleanup_config = SessionConfig(ttl_seconds=5, cleanup_interval=1, allow_test_values=True)
        cleanup_manager = SessionManager(cleanup_config)

        # Create session
        cleanup_manager.set_session(phone, thread_id)

        # Have conversation with cleanup running in between
        for i in range(8):  # 8 iterations over ~8 seconds
            time.sleep(1)  # Wait 1 second each iteration

            # Access session (this refreshes TTL)
            retrieved = cleanup_manager.get_session(phone)
            assert retrieved == thread_id, f"Session lost at iteration {i}"

            # Cleanup may have run during this time, but active session should survive
            metrics = cleanup_manager.get_metrics()
            assert metrics['active_sessions'] >= 1, "Active session should survive cleanup"

    def test_ttl_refresh_memory_implications(self):
        """Test that TTL refreshes don't cause memory issues."""
        phone = "memory_test_user"
        thread_id = "thread_memory_test"

        self.session_manager.set_session(phone, thread_id)
        initial_metrics = self.session_manager.get_metrics()

        # Many accesses to refresh TTL
        for i in range(100):
            retrieved = self.session_manager.get_session(phone)
            assert retrieved == thread_id

            # Every 10th access, check metrics haven't grown unexpectedly
            if i % 10 == 0:
                current_metrics = self.session_manager.get_metrics()
                assert current_metrics['active_sessions'] == 1
                # Memory shouldn't grow significantly from just TTL refreshes
                memory_growth = (
                    current_metrics['estimated_memory_bytes']
                    - initial_metrics['estimated_memory_bytes']
                )
                assert memory_growth < 1000, "TTL refreshes causing excessive memory growth"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
