"""Integration utilities for API mocking with rate limiting and validation.

This module provides integration between the mock framework and existing
test infrastructure, including rate limiting integration and validation utilities.
"""

import time
import functools
from typing import Dict, Any, Optional, List, Callable
from contextlib import contextmanager
from unittest.mock import patch

from .mock_framework import mock_manager
from .openai_mocker import openai_mocker, mock_openai_context
from .twilio_mocker import twilio_mocker, mock_twilio_context
from .rate_limiter import RateLimitedTestCase, ServiceRateLimiters


class MockedRateLimitedTestCase(RateLimitedTestCase):
    """Enhanced test base class with both mocking and rate limiting.
    
    This class provides automatic API mocking while maintaining rate limiting
    for cases where real API calls need to be made selectively.
    """
    
    # Default mock scenarios
    DEFAULT_OPENAI_SCENARIO = "successful_conversation"
    DEFAULT_TWILIO_SCENARIO = "successful_messaging"
    
    # Control which APIs to mock
    MOCK_OPENAI = True
    MOCK_TWILIO = True
    
    def setup_method(self, method):
        """Set up mocking and rate limiting for test method."""
        super().setup_method(method)
        
        # Register mockers with global manager
        mock_manager.register_mocker("openai", openai_mocker)
        mock_manager.register_mocker("twilio", twilio_mocker)
        
        # Store active mocks for cleanup
        self._active_mocks = []
    
    def teardown_method(self, method):
        """Clean up mocks after test method."""
        # Stop all active mocks
        for mocker in self._active_mocks:
            if hasattr(mocker, 'stop_mocking'):
                mocker.stop_mocking()
        self._active_mocks.clear()
        
        # Call parent cleanup if exists
        if hasattr(super(), 'teardown_method'):
            super().teardown_method(method)
    
    @contextmanager
    def mock_apis(self, openai_scenario: Optional[str] = None, 
                  twilio_scenario: Optional[str] = None):
        """Context manager for API mocking within tests.
        
        Args:
            openai_scenario: OpenAI mock scenario to activate
            twilio_scenario: Twilio mock scenario to activate
        """
        contexts = []
        
        try:
            # Start OpenAI mocking if enabled
            if self.MOCK_OPENAI and openai_scenario:
                openai_ctx = mock_openai_context(openai_scenario)
                openai_mock = openai_ctx.__enter__()
                contexts.append((openai_ctx, openai_mock))
                self._active_mocks.append(openai_mock)
            
            # Start Twilio mocking if enabled
            if self.MOCK_TWILIO and twilio_scenario:
                twilio_ctx = mock_twilio_context(twilio_scenario)
                twilio_mock = twilio_ctx.__enter__()
                contexts.append((twilio_ctx, twilio_mock))
                self._active_mocks.append(twilio_mock)
            
            yield {
                "openai": openai_mocker if self.MOCK_OPENAI else None,
                "twilio": twilio_mocker if self.MOCK_TWILIO else None
            }
            
        finally:
            # Clean up contexts in reverse order
            for ctx, _ in reversed(contexts):
                ctx.__exit__(None, None, None)
    
    def make_rate_limited_api_call(self, service: str, func: Callable, *args, **kwargs):
        """Make a rate-limited API call with appropriate service configuration.
        
        Args:
            service: Service name ('openai', 'twilio', etc.)
            func: Function to call
            *args, **kwargs: Arguments for the function
        """
        # Use service-specific rate limits
        if service == "openai":
            config = ServiceRateLimiters.OPENAI
        elif service == "twilio":
            config = ServiceRateLimiters.TWILIO
        else:
            config = ServiceRateLimiters.DEFAULT
        
        # Get rate limiter for this service
        from .rate_limiter import get_rate_limiter
        limiter = get_rate_limiter(
            config["service"],
            config["calls_per_second"],
            config["burst_size"]
        )
        
        # Acquire token and make call
        limiter.acquire()
        return func(*args, **kwargs)


def mock_fixture(openai_scenario: str = "successful_conversation",
                twilio_scenario: str = "successful_messaging"):
    """Decorator to create a test fixture with specific mock scenarios.
    
    Args:
        openai_scenario: OpenAI mock scenario to use
        twilio_scenario: Twilio mock scenario to use
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Set up mocks
            openai_mocker.start_mocking()
            openai_mocker.activate_scenario(openai_scenario)
            
            twilio_mocker.start_mocking()
            twilio_mocker.activate_scenario(twilio_scenario)
            
            try:
                # Call the test function
                return func(*args, **kwargs)
            finally:
                # Clean up
                openai_mocker.stop_mocking()
                twilio_mocker.stop_mocking()
        
        return wrapper
    return decorator


def create_conversation_fixture(user_messages: List[str], 
                              assistant_responses: List[str],
                              phone_number: str = "whatsapp:+1234567890") -> Dict[str, Any]:
    """Create a complete conversation fixture for testing.
    
    Args:
        user_messages: List of user messages to send
        assistant_responses: List of expected assistant responses
        phone_number: WhatsApp phone number for the conversation
        
    Returns:
        Dictionary containing fixture data and helper functions
    """
    # Generate consistent IDs for the conversation
    thread_id = f"thread_test_{int(time.time())}"
    
    fixture = {
        "phone_number": phone_number,
        "thread_id": thread_id,
        "user_messages": user_messages,
        "assistant_responses": assistant_responses,
        "webhooks": [],
        "sent_messages": []
    }
    
    # Create webhook payloads for each user message
    for i, message in enumerate(user_messages):
        webhook_data = twilio_mocker.create_webhook_payload(
            phone_number, "whatsapp:+14155238886", message
        )
        fixture["webhooks"].append(webhook_data)
    
    return fixture


class MockValidationError(Exception):
    """Exception raised when mock validation fails."""
    pass


def validate_mock_interactions(openai_expected_calls: Optional[List[str]] = None,
                             twilio_expected_calls: Optional[List[str]] = None):
    """Validate that expected mock interactions occurred.
    
    Args:
        openai_expected_calls: List of expected OpenAI endpoint calls
        twilio_expected_calls: List of expected Twilio endpoint calls
        
    Raises:
        MockValidationError: If expected interactions didn't occur
    """
    # Validate OpenAI interactions
    if openai_expected_calls:
        openai_history = openai_mocker.get_call_history()
        actual_calls = [call["endpoint"] for call in openai_history]
        
        for expected_call in openai_expected_calls:
            if expected_call not in actual_calls:
                raise MockValidationError(
                    f"Expected OpenAI call '{expected_call}' not found. "
                    f"Actual calls: {actual_calls}"
                )
    
    # Validate Twilio interactions
    if twilio_expected_calls:
        twilio_history = twilio_mocker.get_call_history()
        actual_calls = [call["endpoint"] for call in twilio_history]
        
        for expected_call in twilio_expected_calls:
            if expected_call not in actual_calls:
                raise MockValidationError(
                    f"Expected Twilio call '{expected_call}' not found. "
                    f"Actual calls: {actual_calls}"
                )


def reset_all_mocks():
    """Reset all mock states and history."""
    openai_mocker.clear_history()
    twilio_mocker.clear_history()
    
    # Reset internal state
    openai_mocker.assistants.clear()
    openai_mocker.threads.clear()
    openai_mocker.runs.clear()
    openai_mocker.messages.clear()
    
    twilio_mocker.messages.clear()
    twilio_mocker.webhooks.clear()


@contextmanager
def isolated_mock_environment():
    """Context manager providing isolated mock environment for tests."""
    # Store original state
    original_openai_scenario = openai_mocker.active_scenario
    original_twilio_scenario = twilio_mocker.active_scenario
    
    try:
        # Reset everything
        reset_all_mocks()
        
        yield {
            "openai": openai_mocker,
            "twilio": twilio_mocker
        }
        
    finally:
        # Restore original state
        reset_all_mocks()
        
        if original_openai_scenario:
            openai_mocker.activate_scenario(original_openai_scenario)
        if original_twilio_scenario:
            twilio_mocker.activate_scenario(original_twilio_scenario)


# Convenience functions for common test scenarios

def setup_successful_conversation():
    """Set up mocks for a successful end-to-end conversation."""
    openai_mocker.activate_scenario("successful_conversation")
    twilio_mocker.activate_scenario("successful_messaging")


def setup_api_error_scenario():
    """Set up mocks for API error testing."""
    openai_mocker.activate_scenario("api_errors")
    twilio_mocker.activate_scenario("api_errors")


def setup_tool_usage_scenario():
    """Set up mocks for testing tool usage in conversations."""
    openai_mocker.activate_scenario("tool_usage")
    twilio_mocker.activate_scenario("successful_messaging")


# Export commonly used components
__all__ = [
    "MockedRateLimitedTestCase",
    "mock_fixture", 
    "create_conversation_fixture",
    "validate_mock_interactions",
    "reset_all_mocks",
    "isolated_mock_environment",
    "setup_successful_conversation",
    "setup_api_error_scenario", 
    "setup_tool_usage_scenario",
    "MockValidationError"
]