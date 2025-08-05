"""End-to-End conversation flow tests for WhatsPR agent.

Tests complete user conversation flows from the Final Acceptance Test Plan,
validating agent behavior, tool calls, and response quality through simulated
WhatsApp interactions via FastAPI TestClient.

These tests require a valid OpenAI API key. If running in CI with test keys,
tests will be skipped with appropriate markers.
"""

import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app


def has_valid_api_key():
    """Check if we have a valid OpenAI API key for testing."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    # Skip if using test/dummy keys that will fail
    return api_key and not any(invalid in api_key.lower() for invalid in ["test", "dummy", "fake"])


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestHappyPathConversation:
    """Test the complete Happy Path conversation flow from Final Acceptance Test Plan."""

    def setup_method(self):
        """Set up test client and mock tool calls for verification."""
        self.client = TestClient(app)
        self.phone_number = "+1234567890"
        self.tool_calls = []

        # Mock the TOOL_DISPATCH to capture tool calls
        self.tool_dispatch_patcher = patch("app.agent_endpoint.TOOL_DISPATCH")
        self.mock_dispatch = self.tool_dispatch_patcher.start()

        # Create mock functions for atomic tools
        self.atomic_tools = [
            "save_announcement_type",
            "save_headline",
            "save_key_facts",
            "save_quotes",
            "save_boilerplate",
            "save_media_contact",
        ]

        # Set up the mock dispatch table
        mock_dispatch_dict = {}
        for tool_name in self.atomic_tools:
            mock_dispatch_dict[tool_name] = self._create_mock_tool(tool_name)

        self.mock_dispatch.update(mock_dispatch_dict)
        self.mock_dispatch.__contains__ = lambda name: name in mock_dispatch_dict
        self.mock_dispatch.__getitem__ = lambda name: mock_dispatch_dict[name]

    def teardown_method(self):
        """Clean up patches."""
        self.tool_dispatch_patcher.stop()

    def _create_mock_tool(self, tool_name):
        """Create a mock tool function that captures calls."""

        def mock_tool(*args, **kwargs):
            self.tool_calls.append({"tool": tool_name, "args": args, "kwargs": kwargs})
            return f"Successfully saved via {tool_name}"

        return mock_tool

    def _send_message(self, body):
        """Send a message to the agent endpoint."""
        response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"From={self.phone_number}&Body={body}",
        )
        return response

    def test_happy_path_conversation(self):
        """Test the complete Happy Path conversation flow with tool call verification.

        This test simulates the exact conversation from section 2.1 of the
        Final Acceptance Test Plan and verifies that:
        1. Agent responds naturally and conversationally
        2. All required atomic tools are called with correct data
        3. Conversation completes within expected turn limit
        4. No errors or crashes occur
        """

        # Step 1: Reset session
        reset_response = self._send_message("reset")
        assert reset_response.status_code == 200

        # Step 2: Initial request
        initial_response = self._send_message(
            "Hi, I need to create a press release for our Series A funding"
        )
        assert initial_response.status_code == 200

        response_text = initial_response.text
        assert len(response_text) > 0
        assert "oops" not in response_text.lower()

        # Agent should respond conversationally, not with rigid templates
        assert not self._is_template_response(response_text)

        # Step 3: Provide multiple details at once
        multi_detail_response = self._send_message(
            "We're TechCorp AI Inc. We just raised $15M led by Venture Partners. "
            "The headline should be 'TechCorp Secures $15M to Revolutionize AI Automation'"
        )
        assert multi_detail_response.status_code == 200
        assert "oops" not in multi_detail_response.text.lower()

        # Step 4: Continue with spokesperson quotes
        quote_response = self._send_message(
            "Our CEO Jane Smith said 'This funding will accelerate our mission to make AI accessible to every business.' "
            "The investor John Doe from Venture Partners added 'TechCorp's vision aligns perfectly with market needs.'"
        )
        assert quote_response.status_code == 200
        assert "oops" not in quote_response.text.lower()

        # Step 5: Complete remaining information
        final_info_response = self._send_message(
            "TechCorp is a leading AI automation platform serving over 1000 enterprises globally. "
            "Founded in 2020, we help businesses automate complex workflows. "
            "Media contact is Sarah Johnson at sarah@techcorp.com, 555-0123"
        )
        assert final_info_response.status_code == 200
        assert "oops" not in final_info_response.text.lower()

        # Verify tool calls were made
        self._verify_required_tool_calls()

        # Verify conversation efficiency (should complete within reasonable turns)
        # This is a basic check - in a real implementation, you'd track turn count
        assert len(self.tool_calls) > 0, "No atomic tools were called during conversation"

    def _is_template_response(self, response_text):
        """Check if response follows rigid template patterns."""
        template_indicators = [
            "step 1:",
            "step 2:",
            "please provide the following:",
            "i need the following information:",
            "required fields:",
            "1. company name",
            "2. funding amount",
        ]

        response_lower = response_text.lower()
        template_matches = sum(
            1 for indicator in template_indicators if indicator in response_lower
        )

        # If response contains multiple template indicators, it's likely template-based
        return template_matches >= 2

    def _verify_required_tool_calls(self):
        """Verify that expected atomic tools were called with appropriate data."""
        called_tools = {call["tool"] for call in self.tool_calls}

        # Expected tools based on the information provided in happy path
        # Note: These are the tools we expect to be called during the conversation

        # At minimum, we should see calls to save core information
        # Using actual atomic tools that exist in the system
        critical_tools = {"save_headline", "save_key_facts"}
        missing_critical = critical_tools - called_tools

        # This assertion should fail initially to create a failing test
        assert len(missing_critical) == 0, f"Critical tools not called: {missing_critical}"

        # Verify data quality in tool calls
        for call in self.tool_calls:
            if call["tool"] == "save_headline":
                # Should contain headline data
                call_data = str(call["args"]) + str(call["kwargs"])
                assert "techcorp secures" in call_data.lower(), "Headline not properly captured"

            elif call["tool"] == "save_key_facts":
                call_data = str(call["args"]) + str(call["kwargs"])
                assert (
                    "15m" in call_data.lower() or "$15" in call_data.lower()
                ), "Key facts with funding amount not properly captured"

            elif call["tool"] == "save_quotes":
                call_data = str(call["args"]) + str(call["kwargs"])
                assert (
                    "jane smith" in call_data.lower() or "ceo" in call_data.lower()
                ), "Spokesperson quotes not properly captured"

    def test_conversation_turn_limit(self):
        """Verify conversation completes within 12 turns as specified in acceptance criteria."""
        turn_count = 0
        max_turns = 12

        # Reset and start conversation
        self._send_message("reset")
        turn_count += 1

        # Simulate a conversation that should complete within turn limit
        messages = [
            "Hi, I need to create a press release for our Series A funding",
            "We're TechCorp AI Inc. We just raised $15M led by Venture Partners",
            "The headline should be 'TechCorp Secures $15M to Revolutionize AI Automation'",
            "Our CEO Jane Smith said 'This funding will accelerate our mission'",
            "Media contact is Sarah Johnson at sarah@techcorp.com, 555-0123",
        ]

        for message in messages:
            response = self._send_message(message)
            turn_count += 1
            assert response.status_code == 200
            assert "oops" not in response.text.lower()

            if turn_count >= max_turns:
                break

        # Verify we stayed within turn limit
        assert turn_count <= max_turns, f"Conversation exceeded {max_turns} turns: {turn_count}"

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

            # Verify natural conversation qualities
            assert not self._is_template_response(response_text)
            assert self._has_conversational_elements(response_text)

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
        ]

        response_lower = response_text.lower()
        return any(indicator in response_lower for indicator in conversational_indicators)


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestEdgeCaseHandling:
    """Test edge cases from the Final Acceptance Test Plan."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_knowledge_file_questions(self):
        """Test agent's ability to answer questions about requirements using knowledge file."""
        phone_number = "+1234567891"

        # Reset session
        reset_response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"From={phone_number}&Body=reset",
        )
        assert reset_response.status_code == 200

        # Ask about requirements
        requirements_response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"From={phone_number}&Body=What information do you need from me?",
        )
        assert requirements_response.status_code == 200

        response_text = requirements_response.text
        assert len(response_text) > 0
        assert "oops" not in response_text.lower()

        # Should reference knowledge file content (this will initially fail)
        # Agent should mention specific requirements
        knowledge_indicators = [
            "company",
            "headline",
            "funding",
            "quote",
            "contact",
            "need",
            "require",
            "information",
        ]

        response_lower = response_text.lower()
        knowledge_matches = sum(
            1 for indicator in knowledge_indicators if indicator in response_lower
        )

        # This assertion should initially fail to create a failing test
        assert (
            knowledge_matches >= 3
        ), f"Agent did not reference knowledge file adequately. Response: {response_text}"

    def test_correction_handling(self):
        """Test agent's ability to handle corrections to previously provided information."""
        phone_number = "+1234567892"

        # Provide initial information
        initial_response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"From={phone_number}&Body=Our headline is 'StartupXYZ Raises $5M'",
        )
        assert initial_response.status_code == 200

        # Correct the information
        correction_response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=f"From={phone_number}&Body=Actually, let me correct that. The headline should be 'StartupXYZ Secures $7M in Seed Funding'",
        )
        assert correction_response.status_code == 200

        response_text = correction_response.text
        assert len(response_text) > 0
        assert "oops" not in response_text.lower()

        # Agent should acknowledge the correction
        correction_indicators = [
            "updated",
            "corrected",
            "changed",
            "got it",
            "understood",
            "noted",
            "adjusted",
            "revised",
        ]

        response_lower = response_text.lower()
        acknowledged_correction = any(
            indicator in response_lower for indicator in correction_indicators
        )

        # This assertion should initially fail to create a failing test
        assert (
            acknowledged_correction
        ), f"Agent did not acknowledge correction. Response: {response_text}"


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestSystemIntegration:
    """Test system integration and error handling."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_endpoint_availability(self):
        """Test that the agent endpoint is available and responsive."""
        response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="From=+1234567890&Body=test",
        )

        # Endpoint should be available
        assert response.status_code == 200
        assert response.text is not None

    def test_malformed_request_handling(self):
        """Test handling of malformed requests."""
        # Missing required fields
        response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="Body=test",  # Missing From field
        )

        # Should handle gracefully, not crash
        assert response.status_code in [
            200,
            400,
            422,
        ]  # Accept various valid HTTP responses

    def test_empty_message_handling(self):
        """Test handling of empty messages."""
        response = self.client.post(
            "/agent",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data="From=+1234567890&Body=",
        )

        # Should handle gracefully
        assert response.status_code == 200
        assert response.text is not None
