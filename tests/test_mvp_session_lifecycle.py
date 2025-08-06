"""MVP Session Lifecycle Testing.

Tests session management with 2-3 concurrent users simulating realistic
MVP usage patterns for press release creation conversations.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

from app.session_manager import SessionManager, SessionEntry
from app.session_config.session_config import SessionConfig
from tests.utils.rate_limiter import RateLimitedTestCase


class TestMVPSessionLifecycle(RateLimitedTestCase):
    """Test session lifecycle with MVP-realistic concurrent users."""

    def setUp(self):
        """Set up test with shorter TTL for faster testing."""
        # Use shorter TTL for testing (5 minutes instead of 1 hour)
        self.test_config = SessionConfig(
            ttl_seconds=300,  # 5 minutes
            cleanup_interval=30,  # 30 seconds
        )
        self.session_manager = SessionManager(self.test_config)

    def test_concurrent_mvp_users_basic(self):
        """Test 3 concurrent users creating press releases simultaneously."""
        users = ["phone1", "phone2", "phone3"]
        threads = []
        results = {}

        def simulate_user_conversation(phone: str):
            """Simulate realistic press release conversation for one user."""
            conversation_results = []
            
            # Simulate 8 message exchanges (typical PR creation)
            for i in range(8):
                # Get or create session
                thread_id = self.session_manager.get_session(phone)
                if thread_id is None:
                    thread_id = f"thread_{phone}_{int(time.time())}"
                    self.session_manager.set_session(phone, thread_id)
                
                conversation_results.append({
                    'step': i + 1,
                    'thread_id': thread_id,
                    'timestamp': datetime.now(),
                })
                
                # Realistic delay between messages (2-10 seconds)
                time.sleep(0.1)  # Shortened for testing
            
            results[phone] = conversation_results

        # Start 3 concurrent user conversations
        for phone in users:
            thread = threading.Thread(target=simulate_user_conversation, args=(phone,))
            threads.append(thread)
            thread.start()

        # Wait for all conversations to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) == 3
        
        for phone in users:
            user_results = results[phone]
            assert len(user_results) == 8
            
            # Verify session consistency - same thread_id throughout conversation
            thread_ids = [r['thread_id'] for r in user_results]
            assert len(set(thread_ids)) == 1, f"User {phone} had inconsistent thread_ids: {thread_ids}"
            
            # Verify thread_id isolation - different users have different threads
            for other_phone in users:
                if other_phone != phone:
                    other_thread_ids = [r['thread_id'] for r in results[other_phone]]
                    assert thread_ids[0] not in other_thread_ids, f"Thread collision between {phone} and {other_phone}"

    def test_session_persistence_across_time(self):
        """Test session persists across realistic conversation timing."""
        phone = "mvp_user_1"
        
        # Start conversation
        thread_id1 = f"thread_{phone}_initial"
        self.session_manager.set_session(phone, thread_id1)
        
        # Simulate conversation with realistic delays (30 seconds between messages)
        message_times = []
        thread_ids = []
        
        for i in range(5):  # 5 messages over 2+ minutes
            retrieved_thread = self.session_manager.get_session(phone)
            thread_ids.append(retrieved_thread)
            message_times.append(datetime.now())
            
            if i < 4:  # Don't sleep after last message
                time.sleep(0.2)  # Shortened for testing
        
        # Verify same thread throughout conversation
        assert all(tid == thread_id1 for tid in thread_ids), f"Thread inconsistency: {thread_ids}"
        assert len(set(thread_ids)) == 1
        
        # Verify session is still active
        final_thread = self.session_manager.get_session(phone)
        assert final_thread == thread_id1

    def test_session_ttl_expiration(self):
        """Test session expires after TTL and creates new thread."""
        phone = "ttl_test_user"
        
        # Create session with very short TTL for testing
        short_ttl_config = SessionConfig(ttl_seconds=1, cleanup_interval=0.5)
        short_session_manager = SessionManager(short_ttl_config)
        
        # Create initial session
        thread_id1 = "thread_initial"
        short_session_manager.set_session(phone, thread_id1)
        
        # Verify session exists
        retrieved = short_session_manager.get_session(phone)
        assert retrieved == thread_id1
        
        # Wait for TTL expiration
        time.sleep(1.2)  # Wait longer than TTL
        
        # Session should be expired and return None
        expired_thread = short_session_manager.get_session(phone)
        assert expired_thread is None, f"Expected None, got {expired_thread}"
        
        # New session should create different thread
        thread_id2 = "thread_new"
        short_session_manager.set_session(phone, thread_id2)
        retrieved_new = short_session_manager.get_session(phone)
        assert retrieved_new == thread_id2
        assert thread_id2 != thread_id1

    def test_cleanup_during_active_conversations(self):
        """Test cleanup doesn't interfere with active conversations."""
        active_phone = "active_user"
        expired_phone = "expired_user"
        
        # Create session manager with short cleanup interval
        cleanup_config = SessionConfig(ttl_seconds=2, cleanup_interval=0.5)
        cleanup_manager = SessionManager(cleanup_config)
        
        # Create active session
        active_thread = "thread_active"
        cleanup_manager.set_session(active_phone, active_thread)
        
        # Create expired session by manipulating internal state
        expired_thread = "thread_expired"
        expired_time = datetime.now() - timedelta(seconds=3)  # Already expired
        cleanup_manager._sessions[expired_phone] = SessionEntry(
            thread_id=expired_thread,
            created_at=expired_time,
            last_accessed=expired_time
        )
        
        # Verify both sessions exist initially
        assert cleanup_manager.get_session(active_phone) == active_thread
        assert len(cleanup_manager._sessions) == 2
        
        # Access active session to refresh it
        refreshed = cleanup_manager.get_session(active_phone)
        assert refreshed == active_thread
        
        # Force cleanup
        removed_count = cleanup_manager.cleanup_expired_sessions()
        
        # Verify expired session removed, active session preserved
        assert removed_count == 1
        assert cleanup_manager.get_session(active_phone) == active_thread
        assert cleanup_manager.get_session(expired_phone) is None
        assert len(cleanup_manager._sessions) == 1

    def test_mvp_load_simulation(self):
        """Simulate realistic MVP load with session metrics tracking."""
        user_count = 3
        messages_per_user = 6
        
        # Track metrics
        initial_metrics = self.session_manager.get_metrics()
        
        # Simulate multiple users having conversations
        for user_idx in range(user_count):
            phone = f"mvp_user_{user_idx}"
            thread_id = f"thread_user_{user_idx}"
            
            # Each user has a conversation
            for msg_idx in range(messages_per_user):
                if msg_idx == 0:
                    # First message creates session
                    self.session_manager.set_session(phone, thread_id)
                else:
                    # Subsequent messages retrieve session
                    retrieved = self.session_manager.get_session(phone)
                    assert retrieved == thread_id
                
                time.sleep(0.05)  # Small delay between messages
        
        # Verify final state
        final_metrics = self.session_manager.get_metrics()
        
        assert final_metrics['active_sessions'] == user_count
        assert final_metrics['total_sessions_created'] >= user_count
        assert final_metrics['estimated_memory_bytes'] > initial_metrics['estimated_memory_bytes']
        
        # Verify all users still have active sessions
        for user_idx in range(user_count):
            phone = f"mvp_user_{user_idx}"
            thread_id = f"thread_user_{user_idx}"
            retrieved = self.session_manager.get_session(phone)
            assert retrieved == thread_id

    def test_session_isolation_stress(self):
        """Stress test session isolation with rapid concurrent access."""
        user_count = 5
        access_count = 10
        results = {}
        
        def rapid_session_access(phone: str):
            """Rapidly access session to test thread safety."""
            thread_id = f"thread_{phone}"
            access_results = []
            
            # Set initial session
            self.session_manager.set_session(phone, thread_id)
            
            # Rapidly access session
            for i in range(access_count):
                retrieved = self.session_manager.get_session(phone)
                access_results.append(retrieved)
                time.sleep(0.01)  # Very short delay
            
            results[phone] = access_results
        
        # Start concurrent rapid access
        threads = []
        for i in range(user_count):
            phone = f"stress_user_{i}"
            thread = threading.Thread(target=rapid_session_access, args=(phone,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify isolation and consistency
        for i in range(user_count):
            phone = f"stress_user_{i}"
            expected_thread = f"thread_{phone}"
            user_results = results[phone]
            
            # All accesses should return same thread_id
            assert all(result == expected_thread for result in user_results), \
                f"Inconsistent results for {phone}: {user_results}"
            
            # Verify final session state
            final_thread = self.session_manager.get_session(phone)
            assert final_thread == expected_thread


if __name__ == "__main__":
    pytest.main([__file__, "-v"])