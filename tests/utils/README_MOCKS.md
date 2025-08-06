# API Mocking Infrastructure

This directory contains a comprehensive API mocking infrastructure for reliable, fast, and cost-effective testing of the WhatsApp chatbot application.

## Overview

The mocking infrastructure provides:

- **Mock Framework**: Base classes for creating API mocks with configurable scenarios
- **OpenAI Mocker**: Complete mocking of OpenAI Assistants API
- **Twilio Mocker**: Complete mocking of Twilio WhatsApp messaging API
- **Integration Utilities**: Helpers for combining mocks with rate limiting and validation
- **Test Base Classes**: Enhanced test classes with automatic mock management

## Quick Start

### Basic Usage

```python
from tests.utils.mock_integration import MockedRateLimitedTestCase, mock_fixture

class TestMyFeature(MockedRateLimitedTestCase):
    
    @mock_fixture("successful_conversation", "successful_messaging")
    def test_conversation_flow(self):
        # Your test code here - APIs are automatically mocked
        from app.agent_runtime import run_thread
        reply, thread_id, tools = run_thread(None, "Hello")
        assert reply is not None
```

### Context Managers

```python
def test_with_context_manager(self):
    with self.mock_apis("successful_conversation", "successful_messaging"):
        # APIs are mocked within this block
        result = some_api_call()
        assert result is not None
```

### Custom Scenarios

```python
from tests.utils.openai_mocker import openai_mocker
from tests.utils.mock_framework import MockScenario, create_success_response

# Create custom scenario
custom_scenario = MockScenario("my_scenario", "Custom test scenario")
custom_scenario.add_response(
    "assistants.create", 
    create_success_response({"id": "custom_assistant", "name": "Custom"})
)

openai_mocker.add_scenario(custom_scenario)
openai_mocker.activate_scenario("my_scenario")
```

## Components

### 1. Mock Framework (`mock_framework.py`)

Base classes and utilities for creating mock APIs:

- `MockResponse`: Represents API responses with metadata
- `MockScenario`: Groups related responses for test scenarios  
- `BaseMocker`: Base class for service-specific mockers
- `MockManager`: Central coordination of multiple mockers

### 2. OpenAI Mocker (`openai_mocker.py`)

Complete mocking of OpenAI APIs used in the application:

**Features:**
- Assistant creation and management
- Thread and message handling
- Run lifecycle (queued → running → completed)
- Tool calling scenarios
- Error conditions and rate limiting

**Scenarios:**
- `successful_conversation`: Complete successful flow
- `api_errors`: Various error conditions
- `tool_usage`: Conversations involving tool calls

**Usage:**
```python
from tests.utils.openai_mocker import mock_openai_context

with mock_openai_context("successful_conversation"):
    # OpenAI calls are mocked
    thread_id = create_thread()
```

### 3. Twilio Mocker (`twilio_mocker.py`)

Complete mocking of Twilio WhatsApp messaging:

**Features:**
- Message sending and status tracking
- Webhook payload simulation
- Media handling
- Error scenarios and rate limiting

**Scenarios:**
- `successful_messaging`: Normal message flow
- `api_errors`: API failures
- `message_failures`: Delivery failures

**Usage:**
```python
from tests.utils.twilio_mocker import twilio_mocker

# Simulate incoming webhook
webhook_data = twilio_mocker.simulate_webhook(
    from_number="whatsapp:+1234567890",
    to_number="whatsapp:+14155238886", 
    body="Hello"
)
```

### 4. Integration Utilities (`mock_integration.py`)

Helpers for integrating mocks with existing test infrastructure:

**Key Classes:**
- `MockedRateLimitedTestCase`: Test base class with mocks and rate limiting
- Various helper functions and context managers

**Features:**
- Automatic mock setup/teardown
- Rate limiting integration
- Validation utilities
- Conversation fixture generation

## Available Scenarios

### OpenAI Scenarios

1. **`successful_conversation`**: Complete successful conversation flow
   - Assistant creation ✓
   - Thread creation ✓  
   - Message handling ✓
   - Run completion ✓
   - Response retrieval ✓

2. **`api_errors`**: Error conditions
   - Rate limiting (429) ✓
   - Authentication errors (401) ✓
   - Invalid requests (400) ✓

3. **`tool_usage`**: Tool calling scenarios
   - Required actions ✓
   - Tool output submission ✓
   - Completion after tools ✓

### Twilio Scenarios

1. **`successful_messaging`**: Normal messaging flow
   - Message creation ✓
   - Status tracking ✓
   - Media handling ✓

2. **`api_errors`**: API failures
   - Rate limiting ✓
   - Invalid parameters ✓
   - Authentication failures ✓

3. **`message_failures`**: Delivery issues
   - Failed messages ✓
   - Undelivered status ✓
   - Error codes ✓

## Best Practices

### 1. Use Appropriate Scenarios

Choose scenarios that match your test objectives:

```python
# For normal functionality testing
@mock_fixture("successful_conversation", "successful_messaging")

# For error handling testing  
@mock_fixture("api_errors", "api_errors")

# For tool functionality testing
@mock_fixture("tool_usage", "successful_messaging")
```

### 2. Validate Mock Interactions

Always verify that expected API calls were made:

```python
from tests.utils.mock_integration import validate_mock_interactions

validate_mock_interactions(
    openai_expected_calls=["threads.create", "threads.runs.create"],
    twilio_expected_calls=["messages.create"]
)
```

### 3. Use Isolated Environments for Complex Tests

For tests that need clean state:

```python
from tests.utils.mock_integration import isolated_mock_environment

with isolated_mock_environment():
    # Clean mock state
    run_complex_test()
```

### 4. Combine with Rate Limiting

The integration automatically handles rate limiting:

```python
class TestWithRateLimit(MockedRateLimitedTestCase):
    CALLS_PER_SECOND = 0.5  # Conservative rate
    
    def test_api_call(self):
        result = self.make_rate_limited_api_call("openai", some_function)
```

## Migrating Existing Tests

### Before (Real API Calls)
```python
def test_conversation(self):
    # Expensive, slow, unreliable
    thread_id = create_thread()  # Real OpenAI call
    reply, _, _ = run_thread(thread_id, "Hello")  # Real OpenAI call
    assert reply is not None
```

### After (Mocked API Calls)
```python
@mock_fixture("successful_conversation")  
def test_conversation(self):
    # Fast, reliable, free
    thread_id = create_thread()  # Mocked call
    reply, _, _ = run_thread(thread_id, "Hello")  # Mocked call
    assert reply is not None
    
    # Additional validation now feasible
    validate_mock_interactions(openai_expected_calls=[
        "threads.create", "threads.messages.create", "threads.runs.create"
    ])
```

## Advanced Usage

### Custom Response Creation

```python
from tests.utils.mock_framework import create_success_response, create_error_response

# Custom success response
custom_response = create_success_response({
    "id": "custom_id",
    "status": "custom_status"
})

# Custom error response  
error_response = create_error_response(
    "custom_error", "Something went wrong", 500
)
```

### Multi-Step Scenarios

```python
scenario = MockScenario("complex_flow", "Complex multi-step flow")

# Add multiple responses for same endpoint (round-robin)
scenario.add_response("threads.runs.retrieve", create_run_response("queued"))
scenario.add_response("threads.runs.retrieve", create_run_response("running"))  
scenario.add_response("threads.runs.retrieve", create_run_response("completed"))
```

### Conversation Fixtures

```python
fixture = create_conversation_fixture(
    user_messages=["Hello", "Tell me about pricing", "Thanks"],
    assistant_responses=["Hi!", "Here's our pricing...", "You're welcome!"],
    phone_number="whatsapp:+1234567890"
)

# Use fixture data in tests
for webhook in fixture["webhooks"]:
    process_webhook(webhook)
```

## Benefits

1. **Speed**: No network calls, instant test execution
2. **Reliability**: No flaky network issues or API outages  
3. **Cost**: No API usage charges during testing
4. **Control**: Exact control over responses and error conditions
5. **Validation**: Verify exact API interactions
6. **Parallelization**: Safe concurrent test execution
7. **Offline**: Tests work without internet connection

## Integration with Existing Infrastructure

The mock infrastructure integrates seamlessly with existing test utilities:

- **Rate Limiting**: Maintains rate limiting for hybrid real/mock scenarios
- **Test Base Classes**: Extends existing `RateLimitedTestCase`
- **Logging**: Compatible with structured logging
- **CI/CD**: Works in all environments without configuration
- **Debugging**: Provides call history and validation tools

This infrastructure enables fast, reliable, and comprehensive testing while reducing external dependencies and costs.