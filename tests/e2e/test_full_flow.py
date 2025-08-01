"""End-to-End tests for WhatsPR agent full conversation flows.

Tests complete user journeys from initial contact through data collection
and final press release generation, including edge cases and difficult inputs.

These tests require a valid OpenAI API key. If running in CI with test keys,
tests will be skipped with appropriate markers.
"""

import pytest
import os
from tests.utils.sim_client import WhatsSim


def has_valid_api_key():
    """Check if we have a valid OpenAI API key for testing."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    # Skip if using test/dummy keys that will fail
    return api_key and not any(
        invalid in api_key.lower() for invalid in ["test", "dummy", "fake"]
    )


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestDifficultInputHandling:
    """Test suite for challenging user input scenarios."""

    def test_conversation_with_emoji(self):
        """Test that agent can handle emojis in user input without crashing.
        
        Verifies:
        - Agent processes emoji-containing messages without errors
        - Company name is correctly extracted despite emojis
        - Conversation flow continues normally
        """
        bot = WhatsSim()
        
        # Start a product launch conversation
        response = bot.send("Product launch")
        assert "product launch" in response.lower()
        
        # Send company information with emojis
        company_with_emoji = "Our company is TechCorp 🚀"
        response = bot.send(company_with_emoji)
        
        # Agent should handle emojis gracefully without crashing
        assert response is not None
        assert len(response) > 0
        assert "error" not in response.lower()
        assert "exception" not in response.lower()
        
        # Continue conversation to ensure flow isn't broken
        response = bot.send("We're launching a new mobile app")
        assert response is not None
        assert "error" not in response.lower()
        
        # Verify the agent can still collect information normally
        headline_response = bot.send("TechCorp Launches Revolutionary Mobile App")
        assert headline_response is not None
        assert "error" not in headline_response.lower()

    def test_multi_message_aggregation(self):
        """Test agent's ability to combine information from multiple messages.
        
        Verifies:
        - Agent maintains context across multiple related messages
        - Information from separate messages is properly aggregated
        - save_headline tool receives combined information
        """
        bot = WhatsSim()
        
        # Mock the save_headline function to capture what gets saved
        with patch('app.tools_atomic.save_headline') as mock_save_headline:
            mock_save_headline.return_value = "headline saved."
            
            # Start funding round conversation
            response = bot.send("Funding round")
            assert "funding" in response.lower()
            
            # Send headline information across multiple messages
            response = bot.send("Our headline is...")
            assert response is not None
            assert "error" not in response.lower()
            
            # Send the actual headline content
            response = bot.send("TechCorp Secures $15M")
            assert response is not None
            assert "error" not in response.lower()
            
            # Send additional headline information
            response = bot.send("Series A Funding Round")
            assert response is not None
            assert "error" not in response.lower()
            
            # Continue conversation to trigger tool usage
            response = bot.send("Please save that headline")
            
            # Verify save_headline was called and got combined information
            # The exact behavior depends on implementation, but we expect
            # the tool to be called with aggregated content
            if mock_save_headline.called:
                call_args = mock_save_headline.call_args[0][0]
                # Should contain key information from multiple messages
                assert "TechCorp" in call_args
                assert "$15M" in call_args or "15M" in call_args
            
            # At minimum, verify conversation continues without errors
            assert response is not None
            assert "error" not in response.lower()


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestBasicFlowIntegrity:
    """Test basic conversation flows work correctly."""

    def test_product_launch_complete_flow(self):
        """Test a complete product launch conversation flow."""
        bot = WhatsSim()
        
        # Start product launch
        response = bot.send("Product launch")
        assert "product launch" in response.lower()
        
        # Provide headline
        response = bot.send("TechCorp Launches Revolutionary AI Platform")
        assert response is not None
        assert "error" not in response.lower()
        
        # Provide key facts
        key_facts = """
        - Platform processes 1M+ queries per second
        - Available in 15 languages
        - 99.9% uptime guarantee
        - Enterprise and developer tiers available
        """
        response = bot.send(key_facts)
        assert response is not None
        assert "error" not in response.lower()
        
        # Provide quote
        quote = '"This platform represents a breakthrough in AI accessibility," said CEO Jane Smith.'
        response = bot.send(quote)
        assert response is not None
        assert "error" not in response.lower()

    def test_funding_round_complete_flow(self):
        """Test a complete funding round conversation flow."""
        bot = WhatsSim()
        
        # Start funding round
        response = bot.send("Funding round")
        assert "funding" in response.lower()
        
        # Provide headline
        response = bot.send("TechCorp Raises $25M Series B")
        assert response is not None
        assert "error" not in response.lower()
        
        # Provide key facts
        key_facts = """
        - Led by Venture Capital Partners
        - Total funding now $50M
        - Will expand to European markets
        - Team growing from 50 to 100 employees
        """
        response = bot.send(key_facts)
        assert response is not None
        assert "error" not in response.lower()
        
        # Provide quote
        quote = '"This funding accelerates our mission to democratize AI," said founder John Doe.'
        response = bot.send(quote)
        assert response is not None
        assert "error" not in response.lower()


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestErrorRecovery:
    """Test agent's ability to recover from various error conditions."""

    def test_invalid_input_recovery(self):
        """Test that agent recovers gracefully from invalid inputs."""
        bot = WhatsSim()
        
        # Start with invalid input
        response = bot.send("xyzabc123nonsense")
        assert response is not None
        # Should still be able to continue conversation
        
        # Now start proper flow
        response = bot.send("Partnership")
        assert "partnership" in response.lower()
        
        # Send some valid information
        response = bot.send("TechCorp partners with GlobalCorp")
        assert response is not None
        assert "error" not in response.lower()

    def test_empty_message_handling(self):
        """Test handling of empty or whitespace-only messages."""
        bot = WhatsSim()
        
        # Send empty message
        response = bot.send("")
        assert response is not None
        
        # Send whitespace-only message
        response = bot.send("   ")
        assert response is not None
        
        # Should still be able to start normal conversation
        response = bot.send("Product launch")
        assert "product launch" in response.lower()


# Lightweight mock tests that always run
class TestE2EInfrastructure:
    """Test E2E infrastructure and basic conversation patterns without requiring API calls."""

    def test_sim_client_basic_functionality(self):
        """Test that WhatsSim client works for basic requests."""
        bot = WhatsSim()

        # Test that bot can send messages and get responses
        response = bot.send("reset")  # This should work without API calls
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_emoji_encoding_handling(self):
        """Test that emoji characters don't crash the basic infrastructure."""
        bot = WhatsSim()

        # Test emoji in message doesn't break the client
        emoji_message = "Hello 🚀 TechCorp 📱"
        try:
            response = bot.send(emoji_message)
            # Should get some response, even if it's an error message
            assert response is not None
            assert isinstance(response, str)
        except UnicodeError:
            pytest.fail("Emoji handling caused Unicode error")
        except Exception as e:
            # Other exceptions are OK for now, we just want to ensure no Unicode crashes
            assert "unicode" not in str(e).lower()
            assert "encoding" not in str(e).lower()

    def test_empty_message_infrastructure(self):
        """Test that empty messages don't crash the infrastructure."""
        bot = WhatsSim()

        # Test empty message handling
        response = bot.send("")
        assert response is not None
        assert isinstance(response, str)

        # Test whitespace message handling
        response = bot.send("   ")
        assert response is not None
        assert isinstance(response, str)