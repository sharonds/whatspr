"""End-to-End conversation flow tests for WhatsPR agent.

Tests complete user conversation flows from the Final Acceptance Test Plan,
validating agent behavior, tool calls, and response quality through
simulated WhatsApp interactions via FastAPI TestClient.
"""

import pytest
import os
import re
from fastapi.testclient import TestClient
from app.main import app
from tests.utils.rate_limiter import RateLimitedTestCase, rate_limit_test


def has_valid_api_key():
    """Check if we have a valid OpenAI API key for testing."""
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key and len(api_key) > 50


def extract_message_content(response_text):
    """Extract message content from XML wrapper."""
    # Look for <Message>content</Message> pattern
    match = re.search(r'<Message>(.*?)</Message>', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text  # Return original if no XML wrapper found


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestHappyPathConversation(RateLimitedTestCase):
    """Test the core happy path conversation flow."""

    # Configure rate limiting for OpenAI API calls
    CALLS_PER_SECOND = 0.3  # ~1 call every 3 seconds
    BURST_SIZE = 2  # Allow 2 calls in quick succession

    def setup_method(self, method):
        """Set up test client and rate limiting."""
        super().setup_method(method)
        self.client = TestClient(app)

    def _send_message(self, body, phone="+12345678901"):
        """Send a message to the agent endpoint with rate limiting."""
        # Apply rate limiting to API calls
        return self.make_api_call(
            lambda: self.client.post(
                "/agent",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=f"From={phone}&Body={body}",
            )
        )

    @rate_limit_test(calls_per_second=0.3, burst_size=2)
    def test_natural_conversation_flow(self):
        """Verify agent maintains natural, conversational responses throughout."""
        self._send_message("reset")

        # Test various conversation patterns
        test_messages = [
            "Hi there, I need help with a press release",
            "Actually, let me start over. We're announcing funding",
            "The amount is $15M and the company is TechCorp",
            "Can you confirm what information you have so far?",
        ]

        for message in test_messages:
            response = self._send_message(message)
            assert response.status_code == 200

            response_text = response.text
            assert len(response_text) > 0
            assert "oops" not in response_text.lower()

            # Extract actual message content from XML wrapper
            message_content = extract_message_content(response_text)
            print(f"\n📝 Message: {message}")
            print(f"🤖 Response: {message_content}")

            # Verify natural conversation qualities
            assert not self._is_template_response(message_content)
            assert self._has_conversational_elements(message_content)

    def _has_conversational_elements(self, response_text):
        """Check if response has natural conversational elements."""
        conversational_indicators = [
            "great",
            "excellent",
            "perfect",
            "thanks",
            "got it",
            "i understand",
            "that helps",
            "i see",
            "wonderful",
            "let me",
            "i'll",
            "sounds good",
            "okay",
            "of course",
            "happy to help",
            "i'd be happy",
            "sure",
            "absolutely",
            "definitely",
            "certainly",
            "what's",
            "how can",
            "what information",
            "exciting",
            "fantastic",
            "amazing",
            "how much",
            "tell me",
            "can you",
            "could you",
            "that's",
            "what",
            "who",
            "where",
            "when",
            "why",
            "how",
        ]

        response_lower = response_text.lower()
        found_indicators = [ind for ind in conversational_indicators if ind in response_lower]
        print(f"🔍 Found conversational indicators: {found_indicators}")
        return len(found_indicators) > 0

    def _is_template_response(self, response_text):
        """Check if response appears to be a template/boilerplate."""
        template_indicators = [
            "please fill in",
            "template",
            "boilerplate",
            "[company name]",
            "[amount]",
            "[insert",
            "placeholder",
            "example:",
            "sample:",
        ]

        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in template_indicators)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
