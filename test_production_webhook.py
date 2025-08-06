#!/usr/bin/env python3
"""Test script to simulate production WhatsApp webhook request.

This script tests the agent endpoint with the exact same data format
that Twilio sends in production to identify why messages aren't getting responses.
"""

import asyncio
from fastapi.datastructures import FormData
from app.agent_endpoint import agent_hook
import structlog

# Configure logging to see what's happening
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class MockRequest:
    """Mock request object that mimics FastAPI Request."""

    def __init__(self, form_data: dict):
        self._form_data = form_data

    async def form(self):
        """Return form data as FormData object."""
        return FormData(self._form_data)


async def test_production_webhook():
    """Test the webhook with production data from the logged request."""

    # Parse the actual production webhook data
    webhook_data = {
        'SmsMessageSid': 'SM7f5188c5ac4d373646e2826168d65044',
        'NumMedia': '0',
        'ProfileName': 'Sharon Sciammas',
        'MessageType': 'text',
        'SmsSid': 'SM7f5188c5ac4d373646e2826168d65044',
        'WaId': '31621366440',
        'SmsStatus': 'received',
        'Body': 'Sharon Sciammas',  # This is the actual message content
        'To': 'whatsapp:+14155238886',
        'NumSegments': '1',
        'ReferralNumMedia': '0',
        'MessageSid': 'SM7f5188c5ac4d373646e2826168d65044',
        'AccountSid': 'ACTEST123456789012345678901234567890',
        'From': 'whatsapp:+31621366440',
        'ApiVersion': '2010-04-01',
    }

    print("🧪 Testing production webhook with data:")
    print(f"From: {webhook_data['From']}")
    print(f"Body: '{webhook_data['Body']}'")
    print(f"ProfileName: {webhook_data['ProfileName']}")
    print("=" * 50)

    # Create mock request
    mock_request = MockRequest(webhook_data)

    try:
        # Call the agent endpoint
        print("📞 Calling agent_hook...")
        response = await agent_hook(mock_request)

        print("✅ Response received:")
        print(f"Response type: {type(response)}")
        print(f"Response content: {response}")

        # If it's a TwiML response, try to extract the message
        if hasattr(response, 'body'):
            print(f"Response body: {response.body}")

        return response

    except Exception as e:
        print(f"❌ Error during webhook processing: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return None


async def test_simple_message():
    """Test with a simple message like 'hello'."""

    webhook_data = {
        'From': 'whatsapp:+31621366440',
        'Body': 'hello',
        'ProfileName': 'Sharon Sciammas',
        'SmsStatus': 'received',
        'MessageType': 'text',
    }

    print("\n🧪 Testing simple 'hello' message:")
    print("=" * 50)

    mock_request = MockRequest(webhook_data)

    try:
        response = await agent_hook(mock_request)
        print("✅ Simple message response:")
        print(f"Response: {response}")
        return response

    except Exception as e:
        print(f"❌ Error with simple message: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_menu_command():
    """Test menu/reset command."""

    webhook_data = {
        'From': 'whatsapp:+31621366440',
        'Body': 'menu',
        'ProfileName': 'Sharon Sciammas',
        'SmsStatus': 'received',
        'MessageType': 'text',
    }

    print("\n🧪 Testing 'menu' command:")
    print("=" * 50)

    mock_request = MockRequest(webhook_data)

    try:
        response = await agent_hook(mock_request)
        print("✅ Menu command response:")
        print(f"Response: {response}")
        return response

    except Exception as e:
        print(f"❌ Error with menu command: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("🚀 Starting production webhook test...")

    # Test all scenarios
    asyncio.run(test_menu_command())
    asyncio.run(test_simple_message())
    asyncio.run(test_production_webhook())

    print("\n🏁 Test completed!")
