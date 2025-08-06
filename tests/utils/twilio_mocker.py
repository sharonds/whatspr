"""Twilio API mocking utilities for reliable testing.

This module provides comprehensive mocking for Twilio API calls, including
WhatsApp messaging, webhook validation, and related functionality used in the
WhatsApp chatbot application.
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from urllib.parse import parse_qs

from .mock_framework import BaseMocker, MockResponse, MockScenario, create_error_response, create_success_response


@dataclass
class TwilioMessage:
    """Mock Twilio message structure."""
    sid: str
    account_sid: str
    from_: str
    to: str
    body: str
    status: str
    date_created: str
    date_sent: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TwilioWebhookRequest:
    """Mock Twilio webhook request structure."""
    MessageSid: str
    From: str
    To: str
    Body: str
    AccountSid: str
    NumMedia: str = "0"
    ProfileName: Optional[str] = None
    WaId: Optional[str] = None


class TwilioMocker(BaseMocker):
    """Mock manager for Twilio API calls."""
    
    def __init__(self):
        super().__init__()
        self.messages: Dict[str, TwilioMessage] = {}
        self.webhooks: List[TwilioWebhookRequest] = []
        self.patches = []
        
    def create_message_response(self, to: str, body: str, from_: str = "whatsapp:+14155238886",
                              status: str = "sent") -> MockResponse:
        """Create mock message send response."""
        message_sid = f"SM{uuid.uuid4().hex[:32]}"
        account_sid = f"AC{uuid.uuid4().hex[:32]}"
        
        message = TwilioMessage(
            sid=message_sid,
            account_sid=account_sid,
            from_=from_,
            to=to,
            body=body,
            status=status,
            date_created=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            date_sent=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) if status == "sent" else None
        )
        
        self.messages[message_sid] = message
        
        return create_success_response({
            "sid": message_sid,
            "account_sid": account_sid,
            "from": from_,
            "to": to,
            "body": body,
            "status": status,
            "date_created": message.date_created,
            "date_sent": message.date_sent,
            "error_code": None,
            "error_message": None,
            "uri": f"/2010-04-01/Accounts/{account_sid}/Messages/{message_sid}.json"
        })
    
    def create_message_fetch_response(self, message_sid: str) -> MockResponse:
        """Create mock message fetch response."""
        if message_sid not in self.messages:
            return create_error_response("not_found", f"Message {message_sid} not found", 404)
        
        message = self.messages[message_sid]
        
        return create_success_response({
            "sid": message.sid,
            "account_sid": message.account_sid,
            "from": message.from_,
            "to": message.to,
            "body": message.body,
            "status": message.status,
            "date_created": message.date_created,
            "date_sent": message.date_sent,
            "error_code": message.error_code,
            "error_message": message.error_message,
            "uri": f"/2010-04-01/Accounts/{message.account_sid}/Messages/{message.sid}.json"
        })
    
    def create_webhook_payload(self, from_number: str, to_number: str, body: str,
                             profile_name: str = "Test User") -> Dict[str, str]:
        """Create mock webhook payload from WhatsApp."""
        message_sid = f"SM{uuid.uuid4().hex[:32]}"
        account_sid = f"AC{uuid.uuid4().hex[:32]}"
        wa_id = from_number.replace("whatsapp:", "").replace("+", "")
        
        webhook_request = TwilioWebhookRequest(
            MessageSid=message_sid,
            From=from_number,
            To=to_number,
            Body=body,
            AccountSid=account_sid,
            NumMedia="0",
            ProfileName=profile_name,
            WaId=wa_id
        )
        
        self.webhooks.append(webhook_request)
        
        # Return as form-encoded data (how Twilio sends webhooks)
        return {
            "MessageSid": message_sid,
            "From": from_number,
            "To": to_number,
            "Body": body,
            "AccountSid": account_sid,
            "NumMedia": "0",
            "ProfileName": profile_name,
            "WaId": wa_id,
            "ApiVersion": "2010-04-01",
            "SmsSid": message_sid,
            "SmsStatus": "received",
            "SmsMessageSid": message_sid
        }
    
    def create_media_response(self, media_content_type: str = "image/jpeg",
                            media_url: str = "https://api.twilio.com/2010-04-01/Accounts/test/Messages/test/Media/test") -> MockResponse:
        """Create mock media fetch response."""
        media_sid = f"ME{uuid.uuid4().hex[:32]}"
        
        return create_success_response({
            "sid": media_sid,
            "content_type": media_content_type,
            "date_created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "date_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "parent_sid": f"SM{uuid.uuid4().hex[:32]}",
            "uri": media_url
        })
    
    def setup_common_scenarios(self):
        """Set up common test scenarios."""
        # Successful messaging scenario
        success_scenario = MockScenario(
            name="successful_messaging",
            description="Successful WhatsApp message sending and receiving"
        )
        
        # Message sending
        success_scenario.add_response("messages.create", 
                                    self.create_message_response("whatsapp:+1234567890", "Test message"))
        
        # Message status fetch
        success_scenario.add_response("messages.fetch",
                                    self.create_message_fetch_response("SM_test"))
        
        # Media handling
        success_scenario.add_response("media.fetch",
                                    self.create_media_response())
        
        self.add_scenario(success_scenario)
        
        # API error scenario
        error_scenario = MockScenario(
            name="api_errors",
            description="Various Twilio API error conditions"
        )
        
        # Rate limit error
        error_scenario.add_response("messages.create",
                                  create_error_response("rate_limit_exceeded",
                                                       "Too many requests", 429))
        
        # Invalid phone number
        error_scenario.add_response("messages.create",
                                  create_error_response("invalid_parameter",
                                                       "Invalid 'To' phone number", 400))
        
        # Authentication error
        error_scenario.add_response("messages.create",
                                  create_error_response("authentication_failed",
                                                       "Invalid credentials", 401))
        
        self.add_scenario(error_scenario)
        
        # Message delivery failure scenario
        failure_scenario = MockScenario(
            name="message_failures",
            description="Message delivery failures and errors"
        )
        
        # Failed message
        failure_scenario.add_response("messages.create",
                                    self.create_message_response("whatsapp:+1234567890", 
                                                               "Test message", status="failed"))
        
        # Undelivered message
        failure_scenario.add_response("messages.fetch",
                                    MockResponse(data={
                                        "sid": "SM_test",
                                        "status": "undelivered",
                                        "error_code": "30008",
                                        "error_message": "Unknown error"
                                    }))
        
        self.add_scenario(failure_scenario)
    
    def start_mocking(self):
        """Start mocking Twilio API calls."""
        # Set up scenarios
        self.setup_common_scenarios()
        
        # Mock the Twilio client
        def mock_twilio_client(*args, **kwargs):
            client_mock = MagicMock()
            
            # Mock messages resource
            def mock_message_create(**create_kwargs):
                return self._mock_api_call("messages.create", **create_kwargs)
            
            def mock_message_fetch(sid, **fetch_kwargs):
                return self._mock_api_call("messages.fetch", sid=sid, **fetch_kwargs)
            
            client_mock.messages.create.side_effect = mock_message_create
            client_mock.messages.get.side_effect = mock_message_fetch
            
            # Mock media resource
            def mock_media_fetch(message_sid, media_sid, **media_kwargs):
                return self._mock_api_call("media.fetch", message_sid=message_sid, 
                                         media_sid=media_sid, **media_kwargs)
            
            client_mock.messages.get().media.list.side_effect = lambda: [
                MagicMock(sid=f"ME{uuid.uuid4().hex[:32]}")
            ]
            
            return client_mock
        
        # Mock request validation
        def mock_request_validator(*args, **kwargs):
            validator_mock = MagicMock()
            validator_mock.validate.return_value = True
            return validator_mock
        
        # Patch both the client and request validator
        from twilio.rest import Client
        from twilio.request_validator import RequestValidator
        
        client_patcher = patch.object(Client, '__new__', side_effect=mock_twilio_client)
        validator_patcher = patch.object(RequestValidator, '__new__', side_effect=mock_request_validator)
        
        client_mock = client_patcher.start()
        validator_mock = validator_patcher.start()
        
        self.patches.extend([client_patcher, validator_patcher])
        
        return client_mock, validator_mock
    
    def stop_mocking(self):
        """Stop all active mocks."""
        for patcher in self.patches:
            patcher.stop()
        self.patches.clear()
    
    def _mock_api_call(self, endpoint: str, **kwargs):
        """Handle a mock API call."""
        response = self.mock_response(endpoint, **kwargs)
        
        if response.error:
            # Twilio raises specific exceptions
            if response.status_code == 429:
                from twilio.base.exceptions import TwilioException
                raise TwilioException("Rate limit exceeded")
            elif response.status_code == 400:
                from twilio.base.exceptions import TwilioException
                raise TwilioException("Invalid parameter")
            elif response.status_code == 401:
                from twilio.base.exceptions import TwilioException
                raise TwilioException("Authentication failed")
            else:
                raise response.error
        
        # Simulate delay if specified
        if response.delay > 0:
            time.sleep(response.delay)
        
        # Return mock object with appropriate attributes
        mock_result = MagicMock()
        
        # Set attributes based on response data
        if isinstance(response.data, dict):
            for key, value in response.data.items():
                setattr(mock_result, key, value)
        
        return mock_result
    
    def simulate_webhook(self, from_number: str, to_number: str, body: str,
                        profile_name: str = "Test User") -> Dict[str, str]:
        """Simulate an incoming WhatsApp webhook."""
        return self.create_webhook_payload(from_number, to_number, body, profile_name)
    
    def get_sent_messages(self) -> List[TwilioMessage]:
        """Get all messages that were 'sent' through the mock."""
        return list(self.messages.values())
    
    def get_webhook_history(self) -> List[TwilioWebhookRequest]:
        """Get history of simulated webhooks."""
        return self.webhooks.copy()


# Global Twilio mocker instance
twilio_mocker = TwilioMocker()


def mock_twilio_context(scenario: str = "successful_messaging"):
    """Context manager for Twilio API mocking."""
    class MockContext:
        def __enter__(self):
            twilio_mocker.start_mocking()
            twilio_mocker.activate_scenario(scenario)
            return twilio_mocker
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            twilio_mocker.stop_mocking()
    
    return MockContext()