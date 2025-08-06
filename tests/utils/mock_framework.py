"""API mocking infrastructure for test reliability and isolation.

This module provides a comprehensive mocking framework for external APIs,
allowing tests to run without making real API calls while maintaining
realistic response patterns and error conditions.
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from unittest.mock import Mock, MagicMock
from contextlib import contextmanager


@dataclass
class MockResponse:
    """Represents a mock API response with metadata."""
    
    data: Any
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    delay: float = 0.0  # Simulate network latency
    error: Optional[Exception] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        if self.error:
            raise self.error
        
        if self.delay > 0:
            time.sleep(self.delay)
            
        return {
            "data": self.data,
            "status_code": self.status_code,
            "headers": self.headers
        }


@dataclass
class MockScenario:
    """Defines a complete mock scenario with multiple API interactions."""
    
    name: str
    description: str
    responses: Dict[str, List[MockResponse]] = field(default_factory=dict)
    call_count: Dict[str, int] = field(default_factory=dict)
    
    def add_response(self, endpoint: str, response: MockResponse):
        """Add a response for a specific endpoint."""
        if endpoint not in self.responses:
            self.responses[endpoint] = []
        self.responses[endpoint].append(response)
    
    def get_next_response(self, endpoint: str) -> Optional[MockResponse]:
        """Get the next response for an endpoint."""
        if endpoint not in self.responses:
            return None
            
        if endpoint not in self.call_count:
            self.call_count[endpoint] = 0
            
        responses = self.responses[endpoint]
        if not responses:
            return None
            
        # Use round-robin if we've exhausted responses
        index = self.call_count[endpoint] % len(responses)
        self.call_count[endpoint] += 1
        
        return responses[index]


class BaseMocker:
    """Base class for API mocking functionality."""
    
    def __init__(self):
        self.scenarios: Dict[str, MockScenario] = {}
        self.active_scenario: Optional[str] = None
        self.call_history: List[Dict[str, Any]] = []
        self.fallback_responses: Dict[str, MockResponse] = {}
    
    def add_scenario(self, scenario: MockScenario):
        """Add a mock scenario."""
        self.scenarios[scenario.name] = scenario
    
    def activate_scenario(self, scenario_name: str):
        """Activate a specific mock scenario."""
        if scenario_name not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        self.active_scenario = scenario_name
        self._reset_call_counts()
    
    def set_fallback_response(self, endpoint: str, response: MockResponse):
        """Set a fallback response for an endpoint when no scenario matches."""
        self.fallback_responses[endpoint] = response
    
    def _reset_call_counts(self):
        """Reset call counts for the active scenario."""
        if self.active_scenario and self.active_scenario in self.scenarios:
            self.scenarios[self.active_scenario].call_count.clear()
    
    def _record_call(self, endpoint: str, **kwargs):
        """Record an API call for debugging and validation."""
        call_record = {
            "timestamp": time.time(),
            "endpoint": endpoint,
            "scenario": self.active_scenario,
            **kwargs
        }
        self.call_history.append(call_record)
    
    def get_call_history(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recorded API calls, optionally filtered by endpoint."""
        if endpoint:
            return [call for call in self.call_history if call["endpoint"] == endpoint]
        return self.call_history.copy()
    
    def clear_history(self):
        """Clear the call history."""
        self.call_history.clear()
    
    def mock_response(self, endpoint: str, **call_kwargs) -> MockResponse:
        """Get the appropriate mock response for an API call."""
        self._record_call(endpoint, **call_kwargs)
        
        # Try to get response from active scenario
        if self.active_scenario:
            scenario = self.scenarios[self.active_scenario]
            response = scenario.get_next_response(endpoint)
            if response:
                return response
        
        # Fall back to default response
        if endpoint in self.fallback_responses:
            return self.fallback_responses[endpoint]
        
        # Return generic success response
        return MockResponse(
            data={"message": f"Mock response for {endpoint}"},
            status_code=200
        )


class MockManager:
    """Central manager for all API mocks."""
    
    def __init__(self):
        self.mockers: Dict[str, BaseMocker] = {}
        self.active_mocks: Dict[str, Any] = {}
    
    def register_mocker(self, name: str, mocker: BaseMocker):
        """Register a service mocker."""
        self.mockers[name] = mocker
    
    def get_mocker(self, name: str) -> BaseMocker:
        """Get a registered mocker."""
        if name not in self.mockers:
            raise ValueError(f"Unknown mocker: {name}")
        return self.mockers[name]
    
    @contextmanager
    def mock_context(self, service_configs: Dict[str, str]):
        """Context manager for activating multiple service mocks.
        
        Args:
            service_configs: Dict mapping service name to scenario name
        """
        # Store original state
        original_scenarios = {}
        
        try:
            # Activate scenarios
            for service, scenario in service_configs.items():
                if service in self.mockers:
                    mocker = self.mockers[service]
                    original_scenarios[service] = mocker.active_scenario
                    mocker.activate_scenario(scenario)
            
            yield self
            
        finally:
            # Restore original state
            for service, original_scenario in original_scenarios.items():
                if service in self.mockers:
                    if original_scenario:
                        self.mockers[service].activate_scenario(original_scenario)
                    else:
                        self.mockers[service].active_scenario = None


# Global mock manager instance
mock_manager = MockManager()


def create_error_response(error_type: str, message: str, status_code: int = 400) -> MockResponse:
    """Helper to create error responses."""
    error_data = {
        "error": {
            "type": error_type,
            "message": message,
            "code": status_code
        }
    }
    return MockResponse(data=error_data, status_code=status_code)


def create_success_response(data: Any, status_code: int = 200) -> MockResponse:
    """Helper to create success responses."""
    return MockResponse(data=data, status_code=status_code)


def create_timeout_response(timeout_after: float = 5.0) -> MockResponse:
    """Helper to create timeout responses."""
    from requests.exceptions import Timeout
    return MockResponse(
        data=None,
        delay=timeout_after,
        error=Timeout("Request timed out")
    )


def create_rate_limit_response() -> MockResponse:
    """Helper to create rate limit error responses."""
    return create_error_response(
        "rate_limit_exceeded",
        "API rate limit exceeded. Please retry after some time.",
        status_code=429
    )