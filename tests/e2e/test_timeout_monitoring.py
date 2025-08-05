"""WhatsApp Timeout Handling and Production Monitoring Tests.

These tests focus on timeout scenarios and implement monitoring
for the production reliability issues reported by the user.
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


def has_valid_api_key():
    """Check if we have a valid OpenAI API key for testing."""
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key and len(api_key) > 50


@pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
class TestTimeoutHandling:
    """Test timeout scenarios and performance monitoring."""

    def setup_method(self):
        """Set up test environment."""
        self.client = TestClient(app)
        self.test_phone = "+15551234567"

    def _send_whatsapp_message_with_timeout(self, body, timeout_seconds=15):
        """Send WhatsApp message with explicit timeout handling."""
        data = {
            "From": self.test_phone,
            "Body": body,
            "MessageSid": f"SM{int(time.time() * 1000)}",
            "NumMedia": "0",
        }

        start_time = time.time()

        try:
            # Set a timeout slightly less than Twilio's limit
            response = self.client.post(
                "/agent",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=data,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            return response, duration, None
        except Exception as e:
            duration = time.time() - start_time
            return None, duration, str(e)

    def test_twilio_timeout_compliance(self):
        """Test that responses consistently stay within Twilio's 15-second limit."""

        # Test various message types that might cause delays
        test_messages = [
            "We raised 250K from Elon Musk",  # The production failure case
            "Our company TechCorp just completed a $50M Series B funding round led by Sequoia Capital",
            "We are announcing the launch of our revolutionary AI product that will transform the industry",
            "Merger announcement: TechCorp is acquiring StartupInc for $100M in an all-cash deal",
            "IPO announcement: We are going public with a $2B valuation on NASDAQ next month",
        ]

        all_passed = True
        timing_results = []

        for i, message in enumerate(test_messages):
            # Reset session for clean state
            self._send_whatsapp_message_with_timeout("reset", timeout_seconds=5)

            response, duration, error = self._send_whatsapp_message_with_timeout(message)

            timing_results.append(
                {
                    'message_num': i + 1,
                    'message': message[:50] + "..." if len(message) > 50 else message,
                    'duration': duration,
                    'success': response is not None and response.status_code == 200,
                    'error': error,
                }
            )

            if response is None or response.status_code != 200:
                all_passed = False
                print(f"❌ Message {i+1} failed: {error}")
            elif duration >= 15.0:
                all_passed = False
                print(f"⏰ Message {i+1} exceeded 15s limit: {duration:.2f}s")
            else:
                print(f"✅ Message {i+1}: {duration:.2f}s - {message[:40]}...")

        # Print summary
        print("\n📊 Timeout compliance summary:")
        avg_duration = sum(r['duration'] for r in timing_results) / len(timing_results)
        max_duration = max(r['duration'] for r in timing_results)
        success_count = sum(1 for r in timing_results if r['success'])

        print(f"   Average duration: {avg_duration:.2f}s")
        print(f"   Maximum duration: {max_duration:.2f}s")
        print(f"   Success rate: {success_count}/{len(timing_results)}")

        # All messages should complete within 15 seconds
        assert all_passed, "Some messages failed or exceeded timeout limits"
        assert max_duration < 15.0, f"Maximum duration {max_duration:.2f}s exceeds 15s limit"
        assert success_count == len(
            timing_results
        ), f"Only {success_count}/{len(timing_results)} messages succeeded"

    def test_openai_api_timeout_handling(self):
        """Test behavior when OpenAI API calls timeout."""

        # Mock the OpenAI client to simulate timeouts
        with patch('app.agent_runtime.get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Simulate a timeout in the run creation
            def slow_run_create(*args, **kwargs):
                time.sleep(16)  # Longer than Twilio's limit
                return MagicMock(id="test_run_id")

            mock_client.beta.threads.runs.create.side_effect = slow_run_create

            response, duration, error = self._send_whatsapp_message_with_timeout(
                "Test timeout scenario", timeout_seconds=15
            )

            # Should timeout gracefully and not hang
            assert duration < 16, f"Request should timeout before 16s, took {duration:.2f}s"

            # If it times out, that's expected behavior with current implementation
            if error:
                assert "timeout" in error.lower() or "timed out" in error.lower()
                print(f"✅ Timeout handled gracefully: {error}")
            else:
                # If it completes, it should be fast
                assert duration < 15.0, f"If completed, should be within 15s, took {duration:.2f}s"
                print(f"✅ Completed within timeout: {duration:.2f}s")

    def test_response_quality_under_time_pressure(self):
        """Test that response quality doesn't degrade under time pressure."""

        # Send messages back-to-back to create time pressure
        messages = [
            "reset",
            "Our company is TechCorp",
            "We raised 250K from Elon Musk",
            "What information do you have?",
        ]

        responses = []
        for i, message in enumerate(messages):
            response, duration, error = self._send_whatsapp_message_with_timeout(message)

            if response and response.status_code == 200:
                responses.append(
                    {'message': message, 'response': response.text, 'duration': duration}
                )

            assert response is not None, f"Message {i+1} failed: {error}"
            assert response.status_code == 200, f"Message {i+1} returned {response.status_code}"
            assert duration < 15.0, f"Message {i+1} took {duration:.2f}s"

        # Check that the final response contains context from earlier messages
        final_response = responses[-1]['response'].lower()
        context_indicators = ["techcorp", "250k", "elon"]
        found_context = [ind for ind in context_indicators if ind in final_response]

        assert (
            len(found_context) >= 2
        ), f"Should maintain context under pressure. Found: {found_context}"
        print(f"✅ Context maintained under time pressure: {found_context}")

    def test_error_monitoring_capabilities(self):
        """Test error monitoring and diagnostic capabilities."""

        # Test various error scenarios
        error_scenarios = [
            ("", "Empty message"),
            ("   ", "Whitespace only"),
            ("💰" * 100, "Long emoji message"),
            ("Test\x00null\x00character", "Null characters"),
        ]

        error_count = 0
        for message, description in error_scenarios:
            response, duration, error = self._send_whatsapp_message_with_timeout(message)

            if error or (response and response.status_code != 200):
                error_count += 1
                print(f"⚠️  {description}: Error detected")
            else:
                print(f"✅ {description}: Handled gracefully")

        # Should handle most scenarios gracefully
        error_rate = error_count / len(error_scenarios)
        assert error_rate < 0.5, f"Too many errors: {error_rate:.2f} (expected < 0.5)"

        print(
            f"📊 Error monitoring results: {error_count}/{len(error_scenarios)} scenarios had errors"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
