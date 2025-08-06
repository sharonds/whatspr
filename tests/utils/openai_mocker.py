"""OpenAI API mocking utilities for reliable testing.

This module provides comprehensive mocking for OpenAI API calls, including
Assistants API, chat completions, and related functionality used in the
WhatsApp chatbot application.
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from .mock_framework import BaseMocker, MockResponse, MockScenario, create_error_response, create_success_response


@dataclass
class OpenAIMessage:
    """Mock OpenAI message structure."""
    id: str
    role: str
    content: List[Dict[str, Any]]
    created_at: int


@dataclass
class OpenAIThread:
    """Mock OpenAI thread structure."""
    id: str
    created_at: int
    metadata: Dict[str, Any]


@dataclass
class OpenAIRun:
    """Mock OpenAI run structure."""
    id: str
    thread_id: str
    assistant_id: str
    status: str
    required_action: Optional[Dict[str, Any]] = None
    last_error: Optional[Dict[str, Any]] = None
    created_at: int = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = int(time.time())


@dataclass
class OpenAIAssistant:
    """Mock OpenAI assistant structure."""
    id: str
    name: str
    instructions: str
    model: str
    tools: List[Dict[str, Any]]
    created_at: int = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = int(time.time())


class OpenAIMocker(BaseMocker):
    """Mock manager for OpenAI API calls."""
    
    def __init__(self):
        super().__init__()
        self.assistants: Dict[str, OpenAIAssistant] = {}
        self.threads: Dict[str, OpenAIThread] = {}
        self.runs: Dict[str, OpenAIRun] = {}
        self.messages: Dict[str, List[OpenAIMessage]] = {}
        self.patches = []
        
    def create_assistant_response(self, name: str = "WhatsPR Agent", 
                                model: str = "gpt-4o-mini") -> MockResponse:
        """Create mock assistant creation response."""
        assistant_id = f"asst_{uuid.uuid4().hex[:24]}"
        assistant = OpenAIAssistant(
            id=assistant_id,
            name=name,
            instructions="Mock assistant for testing",
            model=model,
            tools=[]
        )
        self.assistants[assistant_id] = assistant
        
        return create_success_response({
            "id": assistant_id,
            "object": "assistant",
            "created_at": assistant.created_at,
            "name": assistant.name,
            "description": None,
            "model": assistant.model,
            "instructions": assistant.instructions,
            "tools": assistant.tools,
            "file_ids": [],
            "metadata": {}
        })
    
    def create_thread_response(self) -> MockResponse:
        """Create mock thread creation response."""
        thread_id = f"thread_{uuid.uuid4().hex[:24]}"
        thread = OpenAIThread(
            id=thread_id,
            created_at=int(time.time()),
            metadata={}
        )
        self.threads[thread_id] = thread
        self.messages[thread_id] = []
        
        return create_success_response({
            "id": thread_id,
            "object": "thread",
            "created_at": thread.created_at,
            "metadata": thread.metadata
        })
    
    def create_message_response(self, thread_id: str, role: str = "user", 
                              content: str = "Test message") -> MockResponse:
        """Create mock message creation response."""
        if thread_id not in self.messages:
            self.messages[thread_id] = []
            
        message_id = f"msg_{uuid.uuid4().hex[:24]}"
        message = OpenAIMessage(
            id=message_id,
            role=role,
            content=[{"type": "text", "text": {"value": content}}],
            created_at=int(time.time())
        )
        self.messages[thread_id].append(message)
        
        return create_success_response({
            "id": message_id,
            "object": "thread.message",
            "created_at": message.created_at,
            "thread_id": thread_id,
            "role": role,
            "content": message.content,
            "file_ids": [],
            "assistant_id": None,
            "run_id": None,
            "metadata": {}
        })
    
    def create_run_response(self, thread_id: str, assistant_id: str, 
                          status: str = "queued") -> MockResponse:
        """Create mock run creation response."""
        run_id = f"run_{uuid.uuid4().hex[:24]}"
        run = OpenAIRun(
            id=run_id,
            thread_id=thread_id,
            assistant_id=assistant_id,
            status=status
        )
        self.runs[run_id] = run
        
        return create_success_response({
            "id": run_id,
            "object": "thread.run",
            "created_at": run.created_at,
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "status": status,
            "required_action": None,
            "last_error": None,
            "expires_at": int(time.time()) + 600,  # 10 minutes
            "started_at": None,
            "cancelled_at": None,
            "failed_at": None,
            "completed_at": None,
            "model": "gpt-4o-mini",
            "instructions": None,
            "tools": [],
            "file_ids": [],
            "metadata": {}
        })
    
    def create_run_retrieve_response(self, thread_id: str, run_id: str,
                                   status: str = "completed") -> MockResponse:
        """Create mock run retrieval response."""
        if run_id in self.runs:
            run = self.runs[run_id]
            run.status = status
        else:
            run = OpenAIRun(
                id=run_id,
                thread_id=thread_id,
                assistant_id="asst_test",
                status=status
            )
            self.runs[run_id] = run
        
        response_data = {
            "id": run_id,
            "object": "thread.run",
            "created_at": run.created_at,
            "thread_id": thread_id,
            "assistant_id": run.assistant_id,
            "status": status,
            "required_action": run.required_action,
            "last_error": run.last_error,
            "expires_at": int(time.time()) + 600,
            "started_at": run.created_at if status != "queued" else None,
            "cancelled_at": None,
            "failed_at": None,
            "completed_at": int(time.time()) if status == "completed" else None,
            "model": "gpt-4o-mini",
            "instructions": None,
            "tools": [],
            "file_ids": [],
            "metadata": {}
        }
        
        return create_success_response(response_data)
    
    def create_messages_list_response(self, thread_id: str, 
                                    assistant_response: str = "Mock assistant response") -> MockResponse:
        """Create mock messages list response with assistant reply."""
        # Add assistant message if not already present
        if thread_id not in self.messages:
            self.messages[thread_id] = []
            
        # Check if we already have an assistant message
        has_assistant_msg = any(msg.role == "assistant" for msg in self.messages[thread_id])
        
        if not has_assistant_msg:
            assistant_msg = OpenAIMessage(
                id=f"msg_{uuid.uuid4().hex[:24]}",
                role="assistant",
                content=[{"type": "text", "text": {"value": assistant_response}}],
                created_at=int(time.time())
            )
            self.messages[thread_id].append(assistant_msg)
        
        # Return messages in reverse chronological order (newest first)
        messages = sorted(self.messages[thread_id], key=lambda m: m.created_at, reverse=True)
        
        response_data = {
            "object": "list",
            "data": [
                {
                    "id": msg.id,
                    "object": "thread.message",
                    "created_at": msg.created_at,
                    "thread_id": thread_id,
                    "role": msg.role,
                    "content": msg.content,
                    "file_ids": [],
                    "assistant_id": "asst_test" if msg.role == "assistant" else None,
                    "run_id": None,
                    "metadata": {}
                }
                for msg in messages
            ],
            "first_id": messages[0].id if messages else None,
            "last_id": messages[-1].id if messages else None,
            "has_more": False
        }
        
        return create_success_response(response_data)
    
    def create_tool_call_run_response(self, thread_id: str, run_id: str, 
                                    tool_calls: List[Dict[str, Any]]) -> MockResponse:
        """Create mock run response requiring action (tool calls)."""
        if run_id in self.runs:
            run = self.runs[run_id]
        else:
            run = OpenAIRun(
                id=run_id,
                thread_id=thread_id,
                assistant_id="asst_test",
                status="requires_action"
            )
            self.runs[run_id] = run
        
        run.status = "requires_action"
        run.required_action = {
            "type": "submit_tool_outputs",
            "submit_tool_outputs": {
                "tool_calls": tool_calls
            }
        }
        
        response_data = {
            "id": run_id,
            "object": "thread.run",
            "created_at": run.created_at,
            "thread_id": thread_id,
            "assistant_id": run.assistant_id,
            "status": "requires_action",
            "required_action": run.required_action,
            "last_error": None,
            "expires_at": int(time.time()) + 600,
            "started_at": run.created_at,
            "cancelled_at": None,
            "failed_at": None,
            "completed_at": None,
            "model": "gpt-4o-mini",
            "instructions": None,
            "tools": [],
            "file_ids": [],
            "metadata": {}
        }
        
        return create_success_response(response_data)
    
    def setup_common_scenarios(self):
        """Set up common test scenarios."""
        # Successful conversation scenario
        success_scenario = MockScenario(
            name="successful_conversation",
            description="Complete successful conversation flow"
        )
        
        # Assistant creation
        success_scenario.add_response("assistants.create", self.create_assistant_response())
        
        # Thread creation
        success_scenario.add_response("threads.create", self.create_thread_response())
        
        # Message creation
        success_scenario.add_response("threads.messages.create", 
                                    self.create_message_response("thread_test", "user"))
        
        # Run creation
        success_scenario.add_response("threads.runs.create",
                                    self.create_run_response("thread_test", "asst_test"))
        
        # Run completion
        success_scenario.add_response("threads.runs.retrieve",
                                    self.create_run_retrieve_response("thread_test", "run_test"))
        
        # Messages list
        success_scenario.add_response("threads.messages.list",
                                    self.create_messages_list_response("thread_test"))
        
        self.add_scenario(success_scenario)
        
        # API error scenario
        error_scenario = MockScenario(
            name="api_errors",
            description="Various API error conditions"
        )
        
        # Rate limit error
        error_scenario.add_response("assistants.create",
                                  create_error_response("rate_limit_exceeded", 
                                                       "Rate limit exceeded", 429))
        
        # Authentication error
        error_scenario.add_response("threads.create",
                                  create_error_response("invalid_api_key",
                                                       "Invalid API key", 401))
        
        self.add_scenario(error_scenario)
        
        # Tool usage scenario
        tool_scenario = MockScenario(
            name="tool_usage",
            description="Conversation with tool calls"
        )
        
        tool_calls = [
            {
                "id": f"call_{uuid.uuid4().hex[:24]}",
                "type": "function",
                "function": {
                    "name": "save_slot",
                    "arguments": json.dumps({"name": "headline", "value": "Test Headline"})
                }
            }
        ]
        
        tool_scenario.add_response("threads.runs.retrieve",
                                 self.create_tool_call_run_response("thread_test", "run_test", tool_calls))
        
        # After tool submission, run completes
        tool_scenario.add_response("threads.runs.submit_tool_outputs",
                                 self.create_run_response("thread_test", "asst_test", "queued"))
        
        tool_scenario.add_response("threads.runs.retrieve",
                                 self.create_run_retrieve_response("thread_test", "run_test", "completed"))
        
        self.add_scenario(tool_scenario)
    
    def start_mocking(self):
        """Start mocking OpenAI API calls."""
        # Set up scenarios
        self.setup_common_scenarios()
        
        # Mock the OpenAI client
        def mock_client():
            client_mock = MagicMock()
            
            # Mock beta.assistants
            client_mock.beta.assistants.create.side_effect = lambda **kwargs: self._mock_api_call(
                "assistants.create", **kwargs
            )
            
            # Mock beta.threads
            client_mock.beta.threads.create.side_effect = lambda **kwargs: self._mock_api_call(
                "threads.create", **kwargs
            )
            
            client_mock.beta.threads.messages.create.side_effect = lambda **kwargs: self._mock_api_call(
                "threads.messages.create", **kwargs
            )
            
            client_mock.beta.threads.messages.list.side_effect = lambda **kwargs: self._mock_api_call(
                "threads.messages.list", **kwargs
            )
            
            # Mock beta.threads.runs
            client_mock.beta.threads.runs.create.side_effect = lambda **kwargs: self._mock_api_call(
                "threads.runs.create", **kwargs
            )
            
            client_mock.beta.threads.runs.retrieve.side_effect = lambda **kwargs: self._mock_api_call(
                "threads.runs.retrieve", **kwargs
            )
            
            client_mock.beta.threads.runs.submit_tool_outputs.side_effect = lambda **kwargs: self._mock_api_call(
                "threads.runs.submit_tool_outputs", **kwargs
            )
            
            return client_mock
        
        # Patch the get_client function
        patcher = patch('app.agent_runtime.get_client', side_effect=mock_client)
        mock_obj = patcher.start()
        self.patches.append(patcher)
        
        return mock_obj
    
    def stop_mocking(self):
        """Stop all active mocks."""
        for patcher in self.patches:
            patcher.stop()
        self.patches.clear()
    
    def _mock_api_call(self, endpoint: str, **kwargs):
        """Handle a mock API call."""
        response = self.mock_response(endpoint, **kwargs)
        
        if response.error:
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


# Global OpenAI mocker instance
openai_mocker = OpenAIMocker()


def mock_openai_context(scenario: str = "successful_conversation"):
    """Context manager for OpenAI API mocking."""
    class MockContext:
        def __enter__(self):
            openai_mocker.start_mocking()
            openai_mocker.activate_scenario(scenario)
            return openai_mocker
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            openai_mocker.stop_mocking()
    
    return MockContext()