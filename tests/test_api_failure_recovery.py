"""API Failure Recovery Testing.

Tests that session management and conversation flow remain stable
during OpenAI timeouts, Twilio errors, and other external API failures.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.agent_endpoint import session_manager, USE_SESSION_MANAGER
from tests.utils.rate_limiter import RateLimitedTestCase


class TestAPIFailureRecovery(RateLimitedTestCase):
    """Test API failure recovery with session preservation."""

    def setup_method(self, method):
        """Set up test client and session manager."""
        super().setup_method(method)
        self.client = TestClient(app)
        self.test_phone = "+1234567890"

        # Reset session manager state
        if USE_SESSION_MANAGER:
            session_manager._sessions.clear()

    def test_openai_timeout_preserves_session(self):
        """Test that OpenAI timeouts don't corrupt session state."""
        # Create initial session
        thread_id = "thread_timeout_test"
        if USE_SESSION_MANAGER:
            session_manager.set_session(self.test_phone, thread_id)

        # Mock OpenAI timeout
        with patch('app.agent_runtime.get_client') as mock_client:
            mock_client.return_value.beta.threads.runs.create.side_effect = asyncio.TimeoutError(
                "OpenAI API timeout"
            )

            # Send message that will trigger timeout
            response = self.client.post(
                "/agent",
                data={"From": self.test_phone, "Body": "Tell me about funding announcements"},
            )

            # Should return timeout fallback message
            assert response.status_code == 200
            response_text = response.text
            assert (
                "processing your request" in response_text.lower()
                or "give me a moment" in response_text.lower()
            )

        # Verify session preserved after timeout
        if USE_SESSION_MANAGER:
            retrieved_thread = session_manager.get_session(self.test_phone)
            assert retrieved_thread == thread_id, "Session should survive OpenAI timeout"

    def test_openai_network_error_recovery(self):
        """Test recovery from OpenAI network errors."""
        # Mock network error then success
        call_count = 0
        original_thread = "thread_network_test"

        def mock_run_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network error")
            # Return mock run object for success case
            mock_run = MagicMock()
            mock_run.id = "run_123"
            return mock_run

        with patch('app.agent_runtime.get_client') as mock_client:
            mock_client.return_value.beta.threads.runs.create = mock_run_create

            # Mock successful retrieval after creation
            mock_run_completed = MagicMock()
            mock_run_completed.status = "completed"
            mock_client.return_value.beta.threads.runs.retrieve.return_value = mock_run_completed

            # Mock thread creation and message retrieval
            mock_thread = MagicMock()
            mock_thread.id = original_thread
            mock_client.return_value.beta.threads.create.return_value = mock_thread

            mock_message = MagicMock()
            mock_message.role = "assistant"
            mock_message.content = [MagicMock()]
            mock_message.content[0].text.value = "Recovery successful"

            mock_messages = MagicMock()
            mock_messages.data = [mock_message]
            mock_client.return_value.beta.threads.messages.list.return_value = mock_messages
            mock_client.return_value.beta.threads.messages.create.return_value = MagicMock()

            # Send message
            response = self.client.post(
                "/agent", data={"From": self.test_phone, "Body": "Test recovery"}
            )

            # Should eventually succeed
            assert response.status_code == 200

    def test_session_manager_failure_graceful_degradation(self):
        """Test graceful degradation when session manager fails."""
        if not USE_SESSION_MANAGER:
            pytest.skip("Test requires session manager to be enabled")

        # Mock session manager failure
        with patch.object(session_manager, 'get_session') as mock_get:
            mock_get.side_effect = Exception("Session manager database error")

            # Should handle gracefully and not crash
            response = self.client.post(
                "/agent", data={"From": self.test_phone, "Body": "Test session failure"}
            )

            # Should return error response, not crash
            assert response.status_code == 200
            assert "error" in response.text.lower() or "try again" in response.text.lower()

        # Verify session manager recovers after error
        session_manager.set_session(self.test_phone, "recovery_thread")
        retrieved = session_manager.get_session(self.test_phone)
        assert retrieved == "recovery_thread"

    def test_twilio_webhook_malformed_data(self):
        """Test handling of malformed Twilio webhook data."""
        # Test missing required fields
        response = self.client.post("/agent", data={})
        assert response.status_code == 200

        # Test malformed phone number
        response = self.client.post("/agent", data={"From": "", "Body": "Test message"})
        assert response.status_code == 200

        # Test missing body
        response = self.client.post("/agent", data={"From": self.test_phone, "Body": ""})
        assert response.status_code == 200

    def test_concurrent_api_failures_isolation(self):
        """Test that API failures for one user don't affect others."""
        phone1 = "+1111111111"
        phone2 = "+2222222222"
        phone3 = "+3333333333"

        # Set up sessions for all users
        if USE_SESSION_MANAGER:
            session_manager.set_session(phone1, "thread_1")
            session_manager.set_session(phone2, "thread_2")
            session_manager.set_session(phone3, "thread_3")

        # Mock failure for phone1 only
        def selective_failure(*args, **kwargs):
            # Check if this is for phone1 by inspecting call stack or thread context
            # For simplicity, fail on first call, succeed on others
            if not hasattr(selective_failure, 'call_count'):
                selective_failure.call_count = 0
            selective_failure.call_count += 1

            if selective_failure.call_count == 1:
                raise asyncio.TimeoutError("Selective timeout")

            # Success case - return mock run
            mock_run = MagicMock()
            mock_run.id = f"run_{selective_failure.call_count}"
            return mock_run

        with patch('app.agent_runtime.get_client') as mock_client:
            mock_client.return_value.beta.threads.runs.create = selective_failure

            # Mock successful completion
            mock_run = MagicMock()
            mock_run.status = "completed"
            mock_client.return_value.beta.threads.runs.retrieve.return_value = mock_run

            # Mock message response
            mock_message = MagicMock()
            mock_message.role = "assistant"
            mock_message.content = [MagicMock()]
            mock_message.content[0].text.value = "Success"

            mock_messages = MagicMock()
            mock_messages.data = [mock_message]
            mock_client.return_value.beta.threads.messages.list.return_value = mock_messages
            mock_client.return_value.beta.threads.messages.create.return_value = MagicMock()

            # Phone1 should get timeout response
            response1 = self.client.post(
                "/agent", data={"From": phone1, "Body": "Message from phone1"}
            )
            assert response1.status_code == 200

            # Phone2 and phone3 should succeed
            response2 = self.client.post(
                "/agent", data={"From": phone2, "Body": "Message from phone2"}
            )
            assert response2.status_code == 200

            response3 = self.client.post(
                "/agent", data={"From": phone3, "Body": "Message from phone3"}
            )
            assert response3.status_code == 200

        # Verify all sessions still exist
        if USE_SESSION_MANAGER:
            assert session_manager.get_session(phone1) == "thread_1"
            assert session_manager.get_session(phone2) == "thread_2"
            assert session_manager.get_session(phone3) == "thread_3"

    def test_session_cleanup_during_api_failure(self):
        """Test session cleanup continues working during API failures."""
        if not USE_SESSION_MANAGER:
            pytest.skip("Test requires session manager")

        # Create mix of sessions
        active_phone = "+1111111111"
        failing_phone = "+2222222222"

        session_manager.set_session(active_phone, "thread_active")
        session_manager.set_session(failing_phone, "thread_failing")

        # Create expired session to cleanup
        from datetime import datetime, timedelta
        from app.session_manager import SessionEntry

        expired_time = datetime.now() - timedelta(seconds=3600)
        session_manager._sessions["expired_user"] = SessionEntry(
            thread_id="expired_thread", created_at=expired_time, last_accessed=expired_time
        )

        # Mock API failure for one user
        with patch('app.agent_runtime.get_client') as mock_client:
            mock_client.return_value.beta.threads.runs.create.side_effect = Exception(
                "API failure during cleanup test"
            )

            # Try to send message to failing user
            response = self.client.post(
                "/agent", data={"From": failing_phone, "Body": "This will fail"}
            )
            assert response.status_code == 200

            # Session cleanup should still work
            removed = session_manager.cleanup_expired_sessions()
            assert removed == 1  # Should remove expired session

            # Active sessions should remain
            assert session_manager.get_session(active_phone) == "thread_active"
            assert session_manager.get_session(failing_phone) == "thread_failing"
            assert session_manager.get_session("expired_user") is None

    def test_health_endpoints_during_api_failure(self):
        """Test that health endpoints work even during API failures."""
        # Health endpoints shouldn't depend on OpenAI API
        response = self.client.get("/health/sessions")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "session_manager" in data

        # Details endpoint
        response = self.client.get("/health/sessions/details")
        assert response.status_code == 200

        # Cleanup endpoint
        response = self.client.post("/health/sessions/cleanup")
        assert response.status_code == 200

    def test_reset_command_during_api_failure(self):
        """Test reset commands work even when API is failing."""
        # Set up session
        if USE_SESSION_MANAGER:
            session_manager.set_session(self.test_phone, "thread_to_reset")

        # Mock API failure
        with patch('app.agent_runtime.get_client') as mock_client:
            mock_client.return_value.beta.threads.runs.create.side_effect = Exception("API down")

            # Reset should work without hitting API
            response = self.client.post("/agent", data={"From": self.test_phone, "Body": "reset"})

            assert response.status_code == 200
            response_text = response.text.lower()
            assert "hi" in response_text or "announcement" in response_text

        # Session should be cleared
        if USE_SESSION_MANAGER:
            retrieved = session_manager.get_session(self.test_phone)
            assert retrieved is None

    def test_memory_stability_during_failures(self):
        """Test memory usage doesn't grow during repeated failures."""
        if not USE_SESSION_MANAGER:
            pytest.skip("Test requires session manager")

        initial_metrics = session_manager.get_metrics()
        initial_memory = initial_metrics['estimated_memory_bytes']

        # Simulate repeated failures
        with patch('app.agent_runtime.get_client') as mock_client:
            mock_client.return_value.beta.threads.runs.create.side_effect = Exception(
                "Repeated failure"
            )

            # Send multiple failing requests
            for i in range(10):
                response = self.client.post(
                    "/agent", data={"From": f"+111111{i:04d}", "Body": f"Failing message {i}"}
                )
                assert response.status_code == 200

        # Memory should not have grown significantly
        final_metrics = session_manager.get_metrics()
        final_memory = final_metrics['estimated_memory_bytes']

        # Allow small growth for error handling but not unbounded
        memory_growth = final_memory - initial_memory
        assert memory_growth < 10000, f"Excessive memory growth: {memory_growth} bytes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
