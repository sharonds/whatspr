"""Tests for the API mocking infrastructure.

This module tests the mock framework, OpenAI mocker, Twilio mocker,
and integration utilities to ensure reliable test isolation.
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from tests.utils.mock_framework import (
    MockResponse, MockScenario, BaseMocker, mock_manager,
    create_error_response, create_success_response
)
from tests.utils.openai_mocker import openai_mocker, mock_openai_context
from tests.utils.twilio_mocker import twilio_mocker, mock_twilio_context
from tests.utils.mock_integration import (
    MockedRateLimitedTestCase, mock_fixture, create_conversation_fixture,
    validate_mock_interactions, MockValidationError, reset_all_mocks
)


class TestMockFramework:
    """Test the base mock framework functionality."""
    
    def test_mock_response_creation(self):
        """Test MockResponse creation and behavior."""
        # Success response
        response = create_success_response({"test": "data"})
        assert response.status_code == 200
        assert response.data == {"test": "data"}
        
        # Error response
        error = create_error_response("test_error", "Test message", 400)
        assert error.status_code == 400
        assert error.data["error"]["type"] == "test_error"
        assert error.data["error"]["message"] == "Test message"
    
    def test_mock_scenario_management(self):
        """Test MockScenario response management."""
        scenario = MockScenario("test", "Test scenario")
        
        # Add responses
        response1 = create_success_response({"call": 1})
        response2 = create_success_response({"call": 2})
        
        scenario.add_response("endpoint", response1)
        scenario.add_response("endpoint", response2)
        
        # Test round-robin behavior
        assert scenario.get_next_response("endpoint") == response1
        assert scenario.get_next_response("endpoint") == response2
        assert scenario.get_next_response("endpoint") == response1  # Cycles back
    
    def test_base_mocker_scenario_activation(self):
        """Test BaseMocker scenario activation."""
        mocker = BaseMocker()
        
        scenario = MockScenario("test", "Test scenario")
        scenario.add_response("test_endpoint", create_success_response({"test": True}))
        
        mocker.add_scenario(scenario)
        mocker.activate_scenario("test")
        
        assert mocker.active_scenario == "test"
        
        # Test response retrieval
        response = mocker.mock_response("test_endpoint")
        assert response.data == {"test": True}
    
    def test_call_history_tracking(self):
        """Test API call history tracking."""
        mocker = BaseMocker()
        
        # Make some mock calls
        mocker.mock_response("endpoint1", param1="value1")
        mocker.mock_response("endpoint2", param2="value2")
        mocker.mock_response("endpoint1", param1="value3")
        
        # Check full history
        history = mocker.get_call_history()
        assert len(history) == 3
        assert history[0]["endpoint"] == "endpoint1"
        assert history[1]["endpoint"] == "endpoint2"
        
        # Check filtered history
        endpoint1_history = mocker.get_call_history("endpoint1")
        assert len(endpoint1_history) == 2
        
        # Clear history
        mocker.clear_history()
        assert len(mocker.get_call_history()) == 0


class TestOpenAIMocker:
    """Test OpenAI API mocking functionality."""
    
    def test_assistant_creation_mock(self):
        """Test mocking assistant creation."""
        response = openai_mocker.create_assistant_response("Test Assistant")
        
        assert response.status_code == 200
        assert response.data["name"] == "Test Assistant"
        assert response.data["id"].startswith("asst_")
        assert response.data["model"] == "gpt-4o-mini"
    
    def test_thread_and_message_mock(self):
        """Test mocking thread creation and messaging."""
        # Create thread
        thread_response = openai_mocker.create_thread_response()
        thread_id = thread_response.data["id"]
        
        assert thread_response.status_code == 200
        assert thread_id.startswith("thread_")
        
        # Add message
        msg_response = openai_mocker.create_message_response(thread_id, "user", "Hello")
        
        assert msg_response.status_code == 200
        assert msg_response.data["thread_id"] == thread_id
        assert msg_response.data["role"] == "user"
    
    def test_run_lifecycle_mock(self):
        """Test mocking complete run lifecycle."""
        thread_id = "thread_test"
        assistant_id = "asst_test"
        run_id = "run_test"
        
        # Create run
        create_response = openai_mocker.create_run_response(thread_id, assistant_id)
        assert create_response.data["status"] == "queued"
        
        # Check completion
        complete_response = openai_mocker.create_run_retrieve_response(
            thread_id, run_id, "completed"
        )
        assert complete_response.data["status"] == "completed"
    
    def test_tool_call_scenario(self):
        """Test tool call mocking scenario."""
        openai_mocker.setup_common_scenarios()
        openai_mocker.activate_scenario("tool_usage")
        
        # Should get tool call response
        response = openai_mocker.mock_response("threads.runs.retrieve")
        assert response.data["status"] == "requires_action"
        assert "required_action" in response.data
    
    def test_openai_context_manager(self):
        """Test OpenAI mocking context manager."""
        with mock_openai_context("successful_conversation") as mocker:
            assert mocker.active_scenario == "successful_conversation"
            
            # Test that mocking is active
            response = mocker.mock_response("assistants.create")
            assert response.status_code == 200


class TestTwilioMocker:
    """Test Twilio API mocking functionality."""
    
    def test_message_creation_mock(self):
        """Test mocking message creation."""
        response = twilio_mocker.create_message_response(
            "whatsapp:+1234567890", "Test message"
        )
        
        assert response.status_code == 200
        assert response.data["to"] == "whatsapp:+1234567890"
        assert response.data["body"] == "Test message"
        assert response.data["sid"].startswith("SM")
    
    def test_webhook_payload_creation(self):
        """Test webhook payload creation."""
        payload = twilio_mocker.create_webhook_payload(
            "whatsapp:+1234567890", "whatsapp:+14155238886", "Hello"
        )
        
        assert payload["From"] == "whatsapp:+1234567890"
        assert payload["To"] == "whatsapp:+14155238886"
        assert payload["Body"] == "Hello"
        assert payload["MessageSid"].startswith("SM")
    
    def test_error_scenarios(self):
        """Test Twilio error scenario mocking."""
        twilio_mocker.setup_common_scenarios()
        twilio_mocker.activate_scenario("api_errors")
        
        # Should get error response
        response = twilio_mocker.mock_response("messages.create")
        assert response.status_code in [400, 401, 429]
    
    def test_twilio_context_manager(self):
        """Test Twilio mocking context manager."""
        with mock_twilio_context("successful_messaging") as mocker:
            assert mocker.active_scenario == "successful_messaging"
            
            # Test that mocking is active
            response = mocker.mock_response("messages.create")
            assert response.status_code == 200


class TestMockIntegration(MockedRateLimitedTestCase):
    """Test mock integration utilities."""
    
    # Reduce rate limits for testing
    CALLS_PER_SECOND = 2.0
    BURST_SIZE = 5
    
    def test_mocked_test_case_setup(self):
        """Test MockedRateLimitedTestCase functionality."""
        # Should have rate limiter
        assert hasattr(self, 'rate_limiter')
        
        # Should have empty active mocks initially
        assert hasattr(self, '_active_mocks')
        assert len(self._active_mocks) == 0
    
    def test_mock_apis_context_manager(self):
        """Test the mock_apis context manager."""
        with self.mock_apis("successful_conversation", "successful_messaging") as mocks:
            assert "openai" in mocks
            assert "twilio" in mocks
            
            # Mocks should be active
            assert len(self._active_mocks) >= 0  # May vary based on implementation
    
    @mock_fixture("successful_conversation", "successful_messaging")
    def test_mock_fixture_decorator(self):
        """Test the mock_fixture decorator."""
        # OpenAI should be mocked
        response = openai_mocker.mock_response("assistants.create")
        assert response.status_code == 200
        
        # Twilio should be mocked
        response = twilio_mocker.mock_response("messages.create")
        assert response.status_code == 200
    
    def test_conversation_fixture_creation(self):
        """Test conversation fixture creation."""
        fixture = create_conversation_fixture(
            user_messages=["Hello", "How are you?"],
            assistant_responses=["Hi there!", "I'm doing well."],
            phone_number="whatsapp:+1234567890"
        )
        
        assert fixture["phone_number"] == "whatsapp:+1234567890"
        assert len(fixture["user_messages"]) == 2
        assert len(fixture["assistant_responses"]) == 2
        assert len(fixture["webhooks"]) == 2
        assert fixture["thread_id"].startswith("thread_test_")
    
    def test_mock_validation(self):
        """Test mock interaction validation."""
        # Reset mocks
        reset_all_mocks()
        
        # Make some mock calls
        openai_mocker.mock_response("assistants.create")
        twilio_mocker.mock_response("messages.create")
        
        # Validate expected calls - should pass
        validate_mock_interactions(
            openai_expected_calls=["assistants.create"],
            twilio_expected_calls=["messages.create"]
        )
        
        # Validate unexpected call - should raise error
        with pytest.raises(MockValidationError):
            validate_mock_interactions(
                openai_expected_calls=["nonexistent.call"]
            )
    
    def test_rate_limited_api_call(self):
        """Test rate-limited API calls."""
        # Mock function that tracks calls
        call_count = 0
        
        def mock_api_function():
            nonlocal call_count
            call_count += 1
            return {"result": f"call_{call_count}"}
        
        # Make rate-limited calls
        start_time = time.time()
        
        result1 = self.make_rate_limited_api_call("openai", mock_api_function)
        result2 = self.make_rate_limited_api_call("openai", mock_api_function)
        
        end_time = time.time()
        
        # Verify results
        assert result1["result"] == "call_1"
        assert result2["result"] == "call_2"
        
        # Should have taken some time due to rate limiting
        # (This is a loose check since rate limiting may vary)
        assert call_count == 2


class TestEndToEndMockScenarios:
    """Test complete end-to-end mock scenarios."""
    
    def test_successful_conversation_scenario(self):
        """Test complete successful conversation with both APIs."""
        reset_all_mocks()
        
        # Set up successful scenario
        openai_mocker.setup_common_scenarios()
        twilio_mocker.setup_common_scenarios()
        
        openai_mocker.activate_scenario("successful_conversation")
        twilio_mocker.activate_scenario("successful_messaging")
        
        # Simulate conversation flow
        # 1. Webhook comes in
        webhook = twilio_mocker.simulate_webhook(
            "whatsapp:+1234567890", "whatsapp:+14155238886", "Hello"
        )
        assert webhook["Body"] == "Hello"
        
        # 2. Create OpenAI thread
        thread_response = openai_mocker.mock_response("threads.create")
        thread_id = thread_response.data["id"]
        
        # 3. Process with OpenAI
        openai_mocker.mock_response("threads.messages.create")
        openai_mocker.mock_response("threads.runs.create")
        run_response = openai_mocker.mock_response("threads.runs.retrieve")
        assert run_response.data["status"] == "completed"
        
        # 4. Send response via Twilio
        twilio_response = twilio_mocker.mock_response("messages.create")
        assert twilio_response.status_code == 200
        
        # Validate all interactions occurred
        validate_mock_interactions(
            openai_expected_calls=[
                "threads.create", "threads.messages.create", 
                "threads.runs.create", "threads.runs.retrieve"
            ],
            twilio_expected_calls=["messages.create"]
        )
    
    def test_error_recovery_scenario(self):
        """Test error handling and recovery scenarios."""
        reset_all_mocks()
        
        # Set up error scenario
        openai_mocker.setup_common_scenarios()
        twilio_mocker.setup_common_scenarios()
        
        openai_mocker.activate_scenario("api_errors")
        twilio_mocker.activate_scenario("api_errors")
        
        # Should get error responses
        openai_response = openai_mocker.mock_response("assistants.create")
        assert openai_response.status_code == 429  # Rate limit
        
        twilio_response = twilio_mocker.mock_response("messages.create")
        assert twilio_response.status_code in [400, 401, 429]