# End-to-End Testing Guide

This document explains the E2E testing framework for WhatsPR, which simulates complete WhatsApp conversations and validates agent behavior.

## 🎯 Overview

The E2E test suite validates:
- Complete conversation flows from initial contact to data collection
- Agent responses and behavior patterns
- Atomic tool integration and calls
- Error handling and edge cases
- Security features (rate limiting, input validation)

## 📁 Test Structure

```
tests/e2e/
├── __init__.py
├── test_conversation_flow.py     # New comprehensive conversation tests
└── test_full_flow.py            # Legacy difficult input tests
```

## 🧪 Test Categories

### 1. Happy Path Conversations (`TestHappyPathConversation`)

Tests the complete flow from the Final Acceptance Test Plan:

```python
def test_happy_path_conversation(self):
    """Simulates the exact 4-step conversation from Final Acceptance Test Plan"""
    # Step 1: Reset session
    # Step 2: Initial funding request  
    # Step 3: Provide multiple details
    # Step 4: Add spokesperson quotes
    # Step 5: Complete remaining info
    
    # Validates:
    # - Natural conversational responses
    # - Atomic tool calls with correct data
    # - No template-style responses
    # - Completion within turn limits
```

**Key Validations:**
- All required atomic tools called (`save_headline`, `save_key_facts`)
- Response quality (conversational vs template-based)
- Data accuracy in tool calls
- Performance (conversation efficiency)

### 2. Edge Case Handling (`TestEdgeCaseHandling`)

Tests challenging scenarios:

```python
def test_knowledge_file_questions(self):
    """Tests agent's ability to answer 'What information do you need?'"""
    
def test_correction_handling(self):
    """Tests handling corrections to previously provided information"""
```

**Scenarios Covered:**
- Questions about requirements (knowledge base integration)
- Corrections and updates to information
- User confusion and clarification requests

### 3. System Integration (`TestSystemIntegration`)

Tests infrastructure and error handling:

```python
def test_endpoint_availability(self):
    """Verifies /agent endpoint responds correctly"""
    
def test_malformed_request_handling(self):
    """Tests handling of invalid requests"""
    
def test_empty_message_handling(self):
    """Tests handling of empty messages"""
```

## 🔧 Test Infrastructure

### Mocking Strategy

The tests use a sophisticated mocking approach:

```python
# Mock the TOOL_DISPATCH to capture tool calls
self.tool_dispatch_patcher = patch("app.agent_endpoint.TOOL_DISPATCH")
self.mock_dispatch = self.tool_dispatch_patcher.start()

# Create mock functions for atomic tools
mock_dispatch_dict = {}
for tool_name in self.atomic_tools:
    mock_dispatch_dict[tool_name] = self._create_mock_tool(tool_name)
```

This approach:
- ✅ Captures actual tool calls as they happen in production
- ✅ Validates tool arguments and data quality
- ✅ Doesn't require API keys for basic functionality tests
- ✅ Tests the actual dispatch mechanism

### FastAPI TestClient Integration

```python
from fastapi.testclient import TestClient
from app.main import app

self.client = TestClient(app)
response = self.client.post(
    "/agent",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data=f"From={phone_number}&Body={message}"
)
```

Benefits:
- Real HTTP requests to actual endpoints
- Complete request/response cycle testing
- Middleware and security feature validation

## 🚀 Running E2E Tests

### Basic Execution

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test class
pytest tests/e2e/test_conversation_flow.py::TestHappyPathConversation -v

# Run with detailed output
pytest tests/e2e/ -v -s
```

### With API Integration

Some tests require valid API keys:

```bash
# Set API key for full integration tests
export OPENAI_API_KEY="sk-your-key-here"
pytest tests/e2e/test_full_flow.py -v
```

Tests automatically skip if API keys are missing or invalid.

## 📊 Test Validation Criteria

### Response Quality Checks

```python
def _is_template_response(self, response_text):
    """Detects rigid template-style responses"""
    template_indicators = [
        "step 1:", "step 2:", "please provide the following:",
        "required fields:", "1. company name"
    ]
    # Fails if response contains multiple template indicators
```

### Conversational Elements

```python
def _has_conversational_elements(self, response_text):
    """Validates natural conversation qualities"""
    conversational_indicators = [
        "great", "excellent", "perfect", "thanks", "got it",
        "i understand", "that helps", "wonderful"
    ]
```

### Tool Call Validation

```python
def _verify_required_tool_calls(self):
    """Verifies atomic tools called with correct data"""
    # Checks that critical tools were called
    critical_tools = {"save_headline", "save_key_facts"}
    
    # Validates data quality in tool arguments  
    for call in self.tool_calls:
        if call["tool"] == "save_headline":
            call_data = str(call["args"]) + str(call["kwargs"])
            assert "techcorp secures" in call_data.lower()
```

## 🐛 Debugging Test Failures

### Common Issues

1. **Tool Calls Not Captured**
   ```bash
   # Check if mocking is working
   assert len(self.tool_calls) > 0, "No atomic tools were called"
   ```

2. **Template Response Detection**
   ```bash
   # Check actual response content
   print(f"Response: {response_text}")
   assert not self._is_template_response(response_text)
   ```

3. **API Key Issues**
   ```bash
   # Tests skip automatically with invalid keys
   @pytest.mark.skipif(not has_valid_api_key(), reason="Requires valid OpenAI API key")
   ```

### Debug Mode

```python
# Add debug prints to see what's happening
def _send_message(self, body):
    response = self.client.post(...)
    print(f"Sent: {body}")
    print(f"Response: {response.text}")
    print(f"Tool calls so far: {len(self.tool_calls)}")
    return response
```

## 🔄 Test Maintenance

### Adding New Test Cases

1. **Create new test method**:
   ```python
   def test_new_scenario(self):
       """Test description"""
       response = self._send_message("test input")
       # Add assertions
   ```

2. **Update atomic tools list** if new tools are added:
   ```python
   self.atomic_tools = [
       "save_announcement_type", "save_headline", 
       "save_key_facts", "save_quotes",
       "save_boilerplate", "save_media_contact",
       "save_new_tool"  # Add new tools here
   ]
   ```

3. **Update validation criteria** as agent behavior evolves

### Performance Considerations

- E2E tests are slower than unit tests (HTTP requests, mocking setup)
- Use `pytest -x` to stop on first failure for faster debugging
- Consider test parallelization for CI environments

## 📈 Success Metrics

A successful E2E test run validates:

- ✅ **Functional**: All conversation flows complete without errors
- ✅ **Behavioral**: Agent responds naturally and conversationally  
- ✅ **Integration**: Atomic tools called with correct data
- ✅ **Security**: Rate limiting and input validation working
- ✅ **Performance**: Conversations complete within turn limits

The E2E test suite provides confidence that the entire system works together correctly from a user's perspective.