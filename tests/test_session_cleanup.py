"""Comprehensive test suite for session cleanup and memory management.

This test suite implements TDD approach for session cleanup feature.
All tests are designed to FAIL initially until implementation is complete.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.agent_endpoint import agent_hook
from app.session_manager import SessionManager
from app.session_config.session_config import SessionConfig
from fastapi import Request
from fastapi.datastructures import FormData


class TestSessionManager:
    """Test the SessionManager class for TTL-based session cleanup."""

    def test_session_manager_initialization(self):
        """Test SessionManager initializes with proper configuration."""
        config = SessionConfig(ttl_seconds=300, cleanup_interval=60)
        manager = SessionManager(config)

        assert manager.config.ttl_seconds == 300
        assert manager.config.cleanup_interval == 60
        assert len(manager._sessions) == 0
        assert manager._last_cleanup is not None

    def test_session_creation_and_retrieval(self):
        """Test basic session creation and retrieval."""
        manager = SessionManager(SessionConfig(ttl_seconds=300, cleanup_interval=60))
        phone = "+1234567890"
        thread_id = "thread_123"

        # Initially no session
        assert manager.get_session(phone) is None

        # Create session
        manager.set_session(phone, thread_id)

        # Retrieve session
        retrieved = manager.get_session(phone)
        assert retrieved == thread_id

    def test_session_ttl_expiration(self):
        """Test sessions expire after TTL period."""
        manager = SessionManager(
            SessionConfig(ttl_seconds=2, cleanup_interval=1, allow_test_values=True)
        )
        phone = "+1234567890"
        thread_id = "thread_123"

        # Create session
        manager.set_session(phone, thread_id)
        assert manager.get_session(phone) == thread_id

        # Wait for expiration
        time.sleep(2.1)

        # Session should be expired and return None
        assert manager.get_session(phone) is None

    def test_session_cleanup_removes_expired_sessions(self):
        """Test cleanup method removes only expired sessions."""
        manager = SessionManager(
            SessionConfig(ttl_seconds=2, cleanup_interval=1, allow_test_values=True)
        )

        # Create multiple sessions
        phones = ["+123456789%d" % i for i in range(5)]
        for i, phone in enumerate(phones):
            manager.set_session(phone, f"thread_{i}")

        assert len(manager._sessions) == 5

        # Wait for expiration
        time.sleep(2.1)

        # Add new session that shouldn't expire
        new_phone = "+9999999999"
        manager.set_session(new_phone, "thread_new")

        # Run cleanup
        removed_count = manager.cleanup_expired_sessions()

        # All old sessions should be removed, new one kept
        assert removed_count == 5
        assert len(manager._sessions) == 1
        assert manager.get_session(new_phone) == "thread_new"

    def test_automatic_cleanup_on_get_session(self):
        """Test cleanup is automatically triggered when accessing sessions."""
        with patch.object(SessionManager, 'cleanup_expired_sessions') as mock_cleanup:
            manager = SessionManager(SessionConfig(ttl_seconds=300, cleanup_interval=60))

            # First access shouldn't trigger cleanup (just initialized)
            manager.get_session("+1234567890")
            mock_cleanup.assert_not_called()

            # Simulate time passing beyond cleanup interval
            manager._last_cleanup = datetime.now() - timedelta(seconds=70)

            # Next access should trigger cleanup
            manager.get_session("+1234567890")
            mock_cleanup.assert_called_once()

    def test_session_count_tracking(self):
        """Test session count tracking for memory monitoring."""
        manager = SessionManager(SessionConfig(ttl_seconds=300))

        assert manager.get_session_count() == 0

        # Add sessions
        for i in range(10):
            manager.set_session(f"+12345678{i:02d}", f"thread_{i}")

        assert manager.get_session_count() == 10

        # Remove some sessions manually
        for i in range(5):
            manager.remove_session(f"+12345678{i:02d}")

        assert manager.get_session_count() == 5

    def test_memory_usage_estimation(self):
        """Test memory usage estimation for monitoring."""
        manager = SessionManager(SessionConfig(ttl_seconds=300))

        # Add sessions with known data sizes
        test_data = [
            ("+1234567890", "thread_" + "x" * 20),  # ~29 bytes thread_id
            ("+9876543210", "thread_" + "y" * 50),  # ~59 bytes thread_id
        ]

        for phone, thread_id in test_data:
            manager.set_session(phone, thread_id)

        memory_bytes = manager.estimate_memory_usage()

        # Should account for phone numbers + thread_ids + overhead
        # Exact calculation depends on implementation but should be > 100 bytes
        assert memory_bytes > 100
        assert memory_bytes < 1000  # Reasonable upper bound for test data


class TestSessionIntegration:
    """Test session cleanup integration with existing agent endpoint."""

    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request."""
        request = MagicMock(spec=Request)
        form_data = FormData([("From", "+1234567890"), ("Body", "Hello test message")])
        request.form.return_value = asyncio.coroutine(lambda: form_data)()
        return request

    @pytest.mark.asyncio
    async def test_session_manager_integration_with_agent_hook(self, mock_request):
        """Test SessionManager integration with existing agent_hook."""
        with patch('app.agent_endpoint.session_manager') as mock_manager:
            mock_manager.get_session.return_value = None
            mock_manager.set_session.return_value = None

            # Mock the AI processing
            with patch('app.agent_endpoint.run_thread_with_retry') as mock_ai:
                mock_ai.return_value = ("Test response", "thread_123", [])

                response = await agent_hook(mock_request)

                # Verify session manager was called
                mock_manager.get_session.assert_called_once_with("+1234567890")
                mock_manager.set_session.assert_called_once_with("+1234567890", "thread_123")

    @pytest.mark.asyncio
    async def test_session_reset_clears_from_manager(self, mock_request):
        """Test reset command clears session from manager."""
        # Update request for reset command
        form_data = FormData([("From", "+1234567890"), ("Body", "reset")])
        mock_request.form.return_value = asyncio.coroutine(lambda: form_data)()

        with patch('app.agent_endpoint.session_manager') as mock_manager:
            response = await agent_hook(mock_request)

            # Verify session was cleared
            mock_manager.remove_session.assert_called_once_with("+1234567890")

    @pytest.mark.asyncio
    async def test_concurrent_session_access_thread_safety(self):
        """Test concurrent access to sessions is thread-safe."""
        manager = SessionManager(SessionConfig(ttl_seconds=300))

        async def concurrent_session_access(phone_suffix):
            phone = f"+123456789{phone_suffix}"
            thread_id = f"thread_{phone_suffix}"

            # Simulate concurrent read/write operations
            for i in range(10):
                manager.set_session(phone, f"{thread_id}_{i}")
                retrieved = manager.get_session(phone)
                assert retrieved is not None
                await asyncio.sleep(0.001)  # Small delay to encourage race conditions

        # Run multiple concurrent tasks
        tasks = [concurrent_session_access(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify final state is consistent
        assert manager.get_session_count() == 5


class TestMemoryLeakPrevention:
    """Test memory leak prevention and monitoring."""

    def test_large_session_volume_cleanup(self):
        """Test system handles large volume of sessions with proper cleanup."""
        manager = SessionManager(SessionConfig(ttl_seconds=0.1, cleanup_interval=0.05))

        # Create large number of sessions
        initial_session_count = 1000
        for i in range(initial_session_count):
            manager.set_session(f"+{i:010d}", f"thread_{i}")

        assert manager.get_session_count() == initial_session_count

        # Wait for expiration
        time.sleep(0.15)

        # Force cleanup by accessing a session
        manager.get_session("+0000000000")

        # All sessions should be cleaned up
        assert manager.get_session_count() == 0

    def test_memory_growth_bounds(self):
        """Test memory usage stays within reasonable bounds."""
        manager = SessionManager(SessionConfig(ttl_seconds=1))

        # Add sessions and measure memory growth
        initial_memory = manager.estimate_memory_usage()

        # Add 100 sessions
        for i in range(100):
            manager.set_session(f"+{i:010d}", f"thread_{i}_{'x' * 20}")

        memory_after_100 = manager.estimate_memory_usage()
        memory_per_session = (memory_after_100 - initial_memory) / 100

        # Add 100 more sessions
        for i in range(100, 200):
            manager.set_session(f"+{i:010d}", f"thread_{i}_{'x' * 20}")

        memory_after_200 = manager.estimate_memory_usage()

        # Memory growth should be approximately linear
        expected_memory = memory_after_100 + (memory_per_session * 100)
        memory_variance = abs(memory_after_200 - expected_memory) / expected_memory

        assert memory_variance < 0.2  # Within 20% variance (accounting for overhead)

    def test_cleanup_performance_under_load(self):
        """Test cleanup performance doesn't degrade significantly under load."""
        manager = SessionManager(SessionConfig(ttl_seconds=0.1))

        # Add many sessions
        session_count = 5000
        for i in range(session_count):
            manager.set_session(f"+{i:010d}", f"thread_{i}")

        # Wait for expiration
        time.sleep(0.15)

        # Measure cleanup performance
        start_time = time.time()
        removed_count = manager.cleanup_expired_sessions()
        cleanup_duration = time.time() - start_time

        assert removed_count == session_count
        assert cleanup_duration < 1.0  # Should complete within 1 second

        # Cleanup rate should be reasonable
        cleanup_rate = removed_count / cleanup_duration
        assert cleanup_rate > 1000  # At least 1000 sessions/second


class TestConfigurationManagement:
    """Test configuration management for session cleanup."""

    def test_session_config_validation(self):
        """Test SessionConfig validates parameters properly."""
        # Valid configuration
        config = SessionConfig(ttl_seconds=300, cleanup_interval=60)
        assert config.ttl_seconds == 300
        assert config.cleanup_interval == 60

        # Invalid TTL (too short)
        with pytest.raises(ValueError, match="TTL must be at least 60 seconds"):
            SessionConfig(ttl_seconds=30)

        # Invalid cleanup interval (too frequent)
        with pytest.raises(ValueError, match="Cleanup interval must be at least 30 seconds"):
            SessionConfig(ttl_seconds=300, cleanup_interval=15)

        # Cleanup interval longer than TTL
        with pytest.raises(ValueError, match="Cleanup interval should be less than TTL"):
            SessionConfig(ttl_seconds=300, cleanup_interval=400)

    def test_environment_variable_configuration(self):
        """Test configuration can be loaded from environment variables."""
        with patch.dict(
            'os.environ', {'SESSION_TTL_SECONDS': '600', 'SESSION_CLEANUP_INTERVAL': '120'}
        ):
            config = SessionConfig.from_env()
            assert config.ttl_seconds == 600
            assert config.cleanup_interval == 120

    def test_default_configuration_values(self):
        """Test default configuration values are reasonable."""
        config = SessionConfig()

        # Defaults should be production-ready
        assert config.ttl_seconds >= 300  # At least 5 minutes
        assert config.cleanup_interval >= 60  # At least 1 minute
        assert config.cleanup_interval < config.ttl_seconds


class TestBackwardCompatibility:
    """Test backward compatibility with existing session management."""

    def test_existing_session_dict_migration(self):
        """Test migration from existing _sessions dict to SessionManager."""
        # Simulate existing sessions dict
        existing_sessions = {
            "+1234567890": "thread_123",
            "+9876543210": "thread_456",
            "+5555555555": None,  # Session without thread
        }

        # Create manager and migrate
        manager = SessionManager(SessionConfig(ttl_seconds=300))
        migrated_count = manager.migrate_from_dict(existing_sessions)

        assert migrated_count == 2  # Only sessions with thread_ids
        assert manager.get_session("+1234567890") == "thread_123"
        assert manager.get_session("+9876543210") == "thread_456"
        assert manager.get_session("+5555555555") is None

    @pytest.mark.asyncio
    async def test_gradual_rollout_compatibility(self, mock_request):
        """Test gradual rollout can fall back to old behavior."""
        with patch('app.agent_endpoint.USE_SESSION_MANAGER', False):
            # Should use old _sessions dict behavior
            with patch('app.agent_endpoint._sessions', {}) as mock_sessions:
                with patch('app.agent_endpoint.run_thread_with_retry') as mock_ai:
                    mock_ai.return_value = ("Test response", "thread_123", [])

                    response = await agent_hook(mock_request)

                    # Should update old _sessions dict
                    assert "+1234567890" in mock_sessions
                    assert mock_sessions["+1234567890"] == "thread_123"


class TestMonitoringAndObservability:
    """Test monitoring and observability features."""

    def test_session_metrics_collection(self):
        """Test collection of session-related metrics."""
        manager = SessionManager(SessionConfig(ttl_seconds=300))

        # Initial metrics
        metrics = manager.get_metrics()
        assert metrics['active_sessions'] == 0
        assert metrics['total_sessions_created'] == 0
        assert metrics['total_sessions_expired'] == 0

        # Create sessions
        for i in range(5):
            manager.set_session(f"+{i:010d}", f"thread_{i}")

        metrics = manager.get_metrics()
        assert metrics['active_sessions'] == 5
        assert metrics['total_sessions_created'] == 5

        # Expire sessions
        manager = SessionManager(SessionConfig(ttl_seconds=0.1))
        for i in range(3):
            manager.set_session(f"+{i:010d}", f"thread_{i}")

        time.sleep(0.15)
        removed = manager.cleanup_expired_sessions()

        metrics = manager.get_metrics()
        assert metrics['total_sessions_expired'] == 3

    def test_cleanup_logging_and_alerts(self):
        """Test proper logging during cleanup operations."""
        with patch('app.session_manager.log') as mock_log:
            manager = SessionManager(SessionConfig(ttl_seconds=0.1))

            # Create and expire sessions
            for i in range(10):
                manager.set_session(f"+{i:010d}", f"thread_{i}")

            time.sleep(0.15)
            removed = manager.cleanup_expired_sessions()

            # Should log cleanup results
            mock_log.info.assert_called()
            log_calls = [call.args[0] for call in mock_log.info.call_args_list]
            assert any('session_cleanup_completed' in call for call in log_calls)
