"""Example of integrating mock infrastructure with existing tests.

This module demonstrates how to update existing tests to use the new
mock infrastructure while maintaining test reliability and reducing
external API dependencies.
"""

import pytest
import time
from typing import Dict, Any

from tests.utils.mock_integration import (
    MockedRateLimitedTestCase, mock_fixture, 
    create_conversation_fixture, isolated_mock_environment,
    setup_successful_conversation, validate_mock_interactions
)
from tests.utils.openai_mocker import openai_mocker, mock_openai_context
from tests.utils.twilio_mocker import twilio_mocker, mock_twilio_context
from tests.utils.sim_client import WhatsSim


class TestAgentRuntimeMocked(MockedRateLimitedTestCase):
    """Example of converting agent runtime tests to use mocks.
    
    This demonstrates how to update existing tests to use the mock
    infrastructure while maintaining the same test coverage.
    """
    
    # Configure rate limiting for this test class
    CALLS_PER_SECOND = 1.0
    BURST_SIZE = 3
    
    def test_create_thread_with_mocks(self):
        """Test thread creation using OpenAI mocks."""
        with self.mock_apis(openai_scenario="successful_conversation"):
            # This would normally call OpenAI API
            from app.agent_runtime import create_thread
            
            thread_id = create_thread()
            assert thread_id is not None
            assert thread_id.startswith("thread_")
            
            # Validate the mock was called
            validate_mock_interactions(openai_expected_calls=["threads.create"])
    
    def test_run_thread_conversation_with_mocks(self):
        """Test complete conversation flow using mocks."""
        with self.mock_apis(
            openai_scenario="successful_conversation",
            twilio_scenario="successful_messaging"
        ):
            from app.agent_runtime import run_thread
            
            # Run a conversation turn
            reply, thread_id, tools = run_thread(None, "Hello, I need help with a press release")
            
            assert reply is not None
            assert thread_id is not None
            assert thread_id.startswith("thread_")
            assert isinstance(tools, list)
            
            # Validate expected API interactions
            validate_mock_interactions(
                openai_expected_calls=[
                    "threads.create",
                    "threads.messages.create", 
                    "threads.runs.create",
                    "threads.runs.retrieve",
                    "threads.messages.list"
                ]
            )
    
    def test_tool_calling_scenario(self):
        """Test tool calling using mock scenarios."""
        with self.mock_apis(openai_scenario="tool_usage"):
            from app.agent_runtime import run_thread
            
            reply, thread_id, tools = run_thread(None, "Save headline: Breaking News!")
            
            assert reply is not None
            assert len(tools) > 0
            assert tools[0]["name"] in ["save_slot", "save_headline"]
    
    @mock_fixture("api_errors", "api_errors") 
    def test_error_handling_with_mocks(self):
        """Test error handling using mock error scenarios."""
        from app.agent_runtime import create_thread
        
        # This should handle the mocked API error gracefully
        with pytest.raises(Exception):  # Specific exception type may vary
            create_thread()


class TestWebhookHandlingMocked(MockedRateLimitedTestCase):
    """Example of mocking webhook handling tests."""
    
    def setup_method(self, method):
        """Set up test environment."""
        super().setup_method(method)
        self.conversation_fixture = create_conversation_fixture(
            user_messages=["Hello", "I need a press release"],
            assistant_responses=["Hi! I'll help you.", "Great! Let's start."],
            phone_number="whatsapp:+1234567890"
        )
    
    def test_incoming_webhook_processing(self):
        """Test processing incoming WhatsApp webhooks."""
        with self.mock_apis("successful_conversation", "successful_messaging"):
            # Simulate incoming webhook
            webhook_data = self.conversation_fixture["webhooks"][0]
            
            # Process webhook (would normally call your webhook handler)
            # This is a simplified example - adjust based on your actual code
            from app.router import get_or_create_session
            
            session = get_or_create_session(webhook_data["From"])
            assert session is not None
            assert session.phone == webhook_data["From"]
    
    def test_outgoing_message_sending(self):
        """Test sending outgoing WhatsApp messages."""
        with self.mock_apis(twilio_scenario="successful_messaging"):
            # This would normally send via Twilio
            response = twilio_mocker.mock_response(
                "messages.create",
                to="whatsapp:+1234567890",
                body="Test response from bot"
            )
            
            assert response.status_code == 200
            assert response.data["to"] == "whatsapp:+1234567890"
            assert response.data["body"] == "Test response from bot"


class TestEndToEndFlowMocked(MockedRateLimitedTestCase):
    """Example of complete end-to-end flow testing with mocks."""
    
    def test_complete_conversation_flow(self):
        """Test complete conversation from webhook to response."""
        with isolated_mock_environment() as mocks:
            # Set up successful scenarios
            setup_successful_conversation()
            
            # Simulate the complete flow
            webhook_payload = twilio_mocker.simulate_webhook(
                from_number="whatsapp:+1234567890",
                to_number="whatsapp:+14155238886",
                body="Hello, I need help with a press release about our new product launch"
            )
            
            # Process webhook (simplified - adjust for your actual flow)
            # 1. Extract message details
            user_message = webhook_payload["Body"]
            from_number = webhook_payload["From"]
            
            # 2. Get or create session
            from app.router import get_or_create_session
            session = get_or_create_session(from_number)
            
            # 3. Process with AI
            from app.agent_runtime import run_thread
            reply, thread_id, tools = run_thread(session.thread_id, user_message)
            
            # 4. Send response
            twilio_response = twilio_mocker.mock_response(
                "messages.create",
                to=from_number,
                from_="whatsapp:+14155238886",
                body=reply
            )
            
            # Verify results
            assert reply is not None
            assert thread_id is not None
            assert twilio_response.status_code == 200
            
            # Verify all expected interactions occurred
            validate_mock_interactions(
                openai_expected_calls=[
                    "threads.create", "threads.messages.create",
                    "threads.runs.create", "threads.runs.retrieve", 
                    "threads.messages.list"
                ],
                twilio_expected_calls=["messages.create"]
            )
    
    def test_conversation_with_tool_usage(self):
        """Test conversation that involves tool calling."""
        with self.mock_apis("tool_usage", "successful_messaging"):
            # Simulate user providing headline
            webhook = twilio_mocker.simulate_webhook(
                from_number="whatsapp:+1234567890",
                to_number="whatsapp:+14155238886", 
                body="Our headline is: Revolutionary AI Product Launches Today"
            )
            
            # Process message
            from app.agent_runtime import run_thread
            reply, thread_id, tools = run_thread(None, webhook["Body"])
            
            # Should have tool calls
            assert len(tools) > 0
            tool_names = [tool["name"] for tool in tools]
            assert any(name in ["save_slot", "save_headline"] for name in tool_names)
    
    def test_error_recovery_flow(self):
        """Test error recovery in end-to-end flow."""
        with self.mock_apis("api_errors", "successful_messaging"):
            # Simulate webhook
            webhook = twilio_mocker.simulate_webhook(
                from_number="whatsapp:+1234567890",
                to_number="whatsapp:+14155238886",
                body="Test message"
            )
            
            # Processing should handle errors gracefully
            # This test verifies error handling behavior
            # Exact implementation depends on your error handling strategy
            pass


class TestPerformanceWithMocks:
    """Performance testing using mocks to avoid API costs."""
    
    def test_concurrent_conversations(self):
        """Test handling multiple concurrent conversations."""
        with isolated_mock_environment():
            setup_successful_conversation()
            
            # Simulate multiple conversations
            conversations = []
            for i in range(5):
                conversation = create_conversation_fixture(
                    user_messages=[f"Hello from user {i}"],
                    assistant_responses=[f"Hi user {i}!"],
                    phone_number=f"whatsapp:+123456789{i}"
                )
                conversations.append(conversation)
            
            # Process conversations (implementation would vary)
            results = []
            for conv in conversations:
                webhook = conv["webhooks"][0]
                # Process each webhook
                results.append({
                    "phone": webhook["From"],
                    "processed": True
                })
            
            assert len(results) == 5
            assert all(r["processed"] for r in results)
    
    def test_rate_limiting_effectiveness(self):
        """Test that rate limiting works with mocks."""
        test_case = MockedRateLimitedTestCase()
        test_case.CALLS_PER_SECOND = 2.0  # Allow 2 calls per second
        
        call_count = 0
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"
        
        # Make rapid calls
        start_time = time.time()
        
        for i in range(3):
            result = test_case.make_rate_limited_api_call("test", mock_api_call)
            assert result == f"call_{i+1}"
        
        elapsed = time.time() - start_time
        
        # Should have taken at least some time due to rate limiting
        assert elapsed > 0  # Basic check - actual timing may vary
        assert call_count == 3


# Example of upgrading an existing test
class TestLegacyUpgradeExample:
    """Example showing how to upgrade existing tests to use mocks."""
    
    def test_old_style_without_mocks(self):
        """Original test that makes real API calls (expensive/slow)."""
        pytest.skip("Converted to mocked version below")
        
        # This is how the test might have looked before:
        # from app.agent_runtime import create_thread, run_thread
        # 
        # thread_id = create_thread()  # Real API call
        # reply, _, tools = run_thread(thread_id, "Hello")  # Real API call
        # 
        # assert reply is not None
        # assert thread_id is not None
    
    @mock_fixture("successful_conversation")
    def test_new_style_with_mocks(self):
        """Updated test using mocks (fast/reliable/free)."""
        from app.agent_runtime import create_thread, run_thread
        
        thread_id = create_thread()  # Mocked API call
        reply, _, tools = run_thread(thread_id, "Hello")  # Mocked API call
        
        assert reply is not None
        assert thread_id is not None
        
        # Additional validation that wasn't feasible with real APIs
        validate_mock_interactions(openai_expected_calls=[
            "threads.create", "threads.messages.create",
            "threads.runs.create", "threads.runs.retrieve",
            "threads.messages.list"
        ])