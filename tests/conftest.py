"""Global test configuration and fixtures for pytest.

Provides shared fixtures for test isolation and state management.
"""

import pytest
import uuid
from unittest.mock import patch, Mock
from app.timeout_config import TimeoutManager
from app.agent_endpoint import session_manager
import app.agent_runtime as agent_runtime


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Reset SessionManager state before each test to ensure isolation."""
    # Clear the session manager's internal state
    session_manager._sessions.clear()
    session_manager._total_sessions_created = 0
    session_manager._total_sessions_expired = 0
    session_manager._last_cleanup = session_manager._last_cleanup.__class__.now()
    yield
    # Clean up after test
    session_manager._sessions.clear()


@pytest.fixture(autouse=True)
def reset_timeout_manager():
    """Reset TimeoutManager singleton state between tests."""
    # Reset the singleton instance to force re-initialization
    TimeoutManager._instance = None
    yield
    # Reset again after test
    TimeoutManager._instance = None


@pytest.fixture
def unique_phone():
    """Generate a unique phone number for each test."""
    test_id = str(uuid.uuid4())[-8:]  # Last 8 chars of UUID
    return f"+1555{test_id}"


@pytest.fixture
def unique_phone_batch():
    """Generate a batch of unique phone numbers for concurrent tests."""

    def _generate_batch(count=5):
        test_id = str(uuid.uuid4())[-6:]  # Last 6 chars of UUID
        return [f"+1555{test_id}{i:02d}" for i in range(count)]

    return _generate_batch


@pytest.fixture(autouse=True)
def reset_openai_client():
    """Reset OpenAI client global state between tests."""
    # Store original client
    _ = agent_runtime._client
    yield
    # Reset to None to force re-initialization in next test
    agent_runtime._client = None


@pytest.fixture
def isolated_test_env():
    """Comprehensive test isolation fixture combining all resets."""
    # This fixture is a combination of all isolation fixtures
    # Use this for tests that need full isolation guarantee
    pass  # The autouse fixtures handle the actual work


@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API calls for reliability testing."""
    with patch('app.agent_runtime.get_client') as mock_get_client:
        # Create mock client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock assistant retrieval
        mock_assistant = Mock()
        mock_assistant.id = "asst_test_123"
        mock_assistant.model = "gpt-4-turbo"
        mock_assistant.tools = [
            Mock(function=Mock(name="save_slot")),
            Mock(function=Mock(name="finish")),
        ]
        mock_client.beta.assistants.retrieve.return_value = mock_assistant

        # Mock thread creation
        mock_thread = Mock()
        mock_thread.id = f"thread_mock_{uuid.uuid4().hex[:8]}"
        mock_client.beta.threads.create.return_value = mock_thread

        yield mock_client


@pytest.fixture
def mock_whatssim_responses():
    """Mock WhatsSim responses for predictable testing."""

    def _mock_response(message_content, has_error=False, response_time=0.5):
        if has_error:
            return "Oops, temporary error. Try again."

        # Simulate realistic responses based on message content
        if "reset" in message_content.lower():
            return "👋 Hi! What kind of announcement?\n  Press 1 for Funding round\n  Press 2 for Product launch\n  Press 3 for Partnership / integration"
        elif message_content.strip() == "1":
            return "Great! You want to announce a funding round. What's your company name?"
        elif "techcorp" in message_content.lower():
            return "Perfect! TechCorp sounds exciting. Tell me about your funding round."
        else:
            return f"Thanks for that information: {message_content[:50]}{'...' if len(message_content) > 50 else ''}. What's next?"

    return _mock_response


@pytest.fixture
def mock_agent_runtime():
    """Mock agent runtime functions for reliability testing."""
    with (
        patch('app.agent_runtime.create_thread') as mock_create,
        patch('app.agent_runtime.run_thread') as mock_run,
        patch('app.agent_endpoint.run_thread_with_retry') as mock_run_retry,
    ):

        # Mock thread creation with unique IDs
        def create_mock_thread():
            return f"thread_mock_{uuid.uuid4().hex[:8]}"

        mock_create.side_effect = create_mock_thread

        # Mock run_thread with realistic responses and tool calls
        def mock_run_thread(thread_id, message):
            # Simulate tool calls for funding announcements
            tool_calls = []
            if any(
                keyword in message.lower()
                for keyword in ["funding", "raised", "million", "techcorp"]
            ):
                tool_calls = [
                    {"name": "save_slot", "arguments": {"name": "company", "value": "TechCorp"}},
                    {
                        "name": "save_slot",
                        "arguments": {"name": "announcement_type", "value": "funding"},
                    },
                ]

            response = f"Thank you for that information about {message[:30]}{'...' if len(message) > 30 else ''}. I'll help you create an announcement."
            return response, thread_id, tool_calls

        mock_run.side_effect = mock_run_thread

        # Mock the retry wrapper to return the same thing
        async def mock_run_thread_retry(thread_id, message, timeout_seconds=25.0):
            return mock_run_thread(thread_id, message)

        mock_run_retry.side_effect = mock_run_thread_retry

        yield {
            "create_thread": mock_create,
            "run_thread": mock_run,
            "run_thread_with_retry": mock_run_retry,
        }
