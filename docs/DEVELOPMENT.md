# Development Guide

This guide covers the development workflow, architecture, and best practices for WhatsPR.

## 🏗️ Project Architecture

### Directory Structure

```
whatspr-staging/
├── app/                          # Main application code
│   ├── agent.py                  # Core agent logic
│   ├── agent_endpoint.py         # WhatsApp webhook endpoint
│   ├── agent_runtime.py          # Agent runtime and tool registration
│   ├── tools_atomic.py           # Atomic tools for data collection
│   ├── security.py               # Security utilities and validation
│   ├── models.py                 # Database models
│   ├── main.py                   # FastAPI application setup
│   └── ...
├── tests/                        # Test suites
│   ├── e2e/                      # End-to-end conversation tests
│   ├── test_tools_atomic.py      # Atomic tools tests
│   ├── test_safety.py            # Security validation tests
│   └── ...
├── prompts/                      # AI agent prompts
│   ├── assistant_v2.txt          # Goal-oriented conversation prompt
│   └── ...
├── knowledge/                    # External knowledge base
│   └── press_release_requirements.txt
├── docs/                         # Documentation
└── flows/                        # YAML flow definitions
```

### Key Components

#### 1. Agent Runtime (`app/agent_runtime.py`)
- Manages OpenAI Assistant integration
- Registers atomic tools with the assistant
- Handles conversation threads and context

#### 2. Atomic Tools (`app/tools_atomic.py`)
- Six specialized functions for structured data collection
- Database persistence with graceful fallback
- Atomic operations with proper error handling

#### 3. Security Layer (`app/security.py`)
- Input validation and sanitization
- Rate limiting (10 requests/minute per phone)
- Security headers and request authentication
- Privacy-preserving logging

#### 4. Agent Endpoint (`app/agent_endpoint.py`)
- WhatsApp webhook handler
- Tool dispatch and execution
- Error handling and logging

## 🔧 Development Workflow

### Setting Up Development Environment

```bash
# 1. Clone and setup Python environment
python -m venv env && source env/bin/activate
pip install -r requirements.txt

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your API keys (NEVER commit this file!)

# 3. Initialize database
python -c "from app.models import init_db; init_db()"

# 4. Verify setup
pytest tests/test_safety.py -v    # Should pass
ruff check app tests              # Should show no errors
```

### Development Server

```bash
# Start with auto-reload
uvicorn app.main:app --reload --port 8000

# For WhatsApp testing
ngrok http 8000
# Copy ngrok URL to Twilio webhook settings
```

### Code Quality Standards

#### Linting and Formatting

```bash
# Check code quality
ruff check app tests

# Format code
ruff format app tests

# Both commands should be run before committing
```

#### Testing Requirements

```bash
# Run all tests
pytest tests/ -v

# Test specific components
pytest tests/test_tools_atomic.py -v     # Atomic tools
pytest tests/e2e/ -v                     # End-to-end flows
pytest tests/test_safety.py -v           # Security validation

# All tests must pass before merging
```

## 🧠 Agent Development

### Atomic Tools Development

When adding new atomic tools:

1. **Define the tool** in `app/tools_atomic.py`:
   ```python
   def save_new_field(value: str) -> str:
       """Saves "new_field" - Description of what this field stores."""
       return _save("new_field", value)
   ```

2. **Register the tool** in `app/agent_runtime.py`:
   ```python
   ATOMIC_FUNCS = [
       "save_announcement_type", "save_headline", "save_key_facts",
       "save_quotes", "save_boilerplate", "save_media_contact",
       "save_new_field"  # Add here
   ]
   ```

3. **Add to tool dispatch** in `app/agent_endpoint.py`:
   ```python
   TOOL_DISPATCH = {
       tools.save_announcement_type: tools.save_announcement_type,
       # ... existing tools ...
       tools.save_new_field: tools.save_new_field,  # Add here
   }
   ```

4. **Update tests**:
   ```python
   # Update test_tools_atomic.py
   required = [
       "save_announcement_type", "save_headline", "save_key_facts",
       "save_quotes", "save_boilerplate", "save_media_contact",
       "save_new_field"  # Add to test
   ]
   ```

### Prompt Engineering

The agent uses `prompts/assistant_v2.txt` for natural conversations:

- **Goal-oriented**: Focuses on collecting information through dialogue
- **Conversational**: Avoids rigid templates or step-by-step instructions
- **Context-aware**: Maintains conversation state across messages
- **Error-tolerant**: Handles corrections and clarifications

### Knowledge Base Integration

External knowledge in `knowledge/press_release_requirements.txt`:

- Provides context for agent responses
- Enables answering "What information do you need?" questions
- Helps with format guidance and validation

## 🔒 Security Development

### Input Validation

Always validate user inputs:

```python
from app.security import SecureMessageRequest

# Validate incoming requests
request_data = SecureMessageRequest(From=phone, Body=message)
# This automatically validates phone format and sanitizes message content
```

### Rate Limiting

Implement rate limiting for new endpoints:

```python
from app.security import validate_request_rate, log_security_event

if not validate_request_rate(phone_number):
    log_security_event("rate_limit_hit", {"endpoint": "/new-endpoint"}, phone_number)
    raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### Secrets Management

**NEVER commit secrets to git:**

```bash
# Check for secrets before committing
grep -r "sk-" . --exclude-dir=.git --exclude-dir=env
grep -r "TWILIO_AUTH_TOKEN" . --exclude-dir=.git --exclude-dir=env

# Should return no results
```

Use environment variables:
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable required")
```

## 🧪 Testing Strategy

### Test Categories

1. **Unit Tests**: Individual component testing
   - `test_tools_atomic.py` - Atomic tools functionality
   - `test_validators.py` - Input validation
   - `test_security.py` - Security utilities

2. **Integration Tests**: Component interaction testing
   - `test_agent.py` - Agent integration
   - `test_router.py` - Request routing

3. **End-to-End Tests**: Complete flow testing
   - `test_conversation_flow.py` - Full conversation simulation
   - `test_full_flow.py` - Difficult input scenarios

4. **Security Tests**: Security feature validation
   - `test_safety.py` - No exposed secrets
   - Rate limiting tests
   - Input validation tests

### Test-Driven Development

When adding new features:

1. **Write failing tests first**:
   ```python
   def test_new_feature():
       # Test the feature that doesn't exist yet
       result = new_feature("input")
       assert result == "expected_output"
   ```

2. **Implement the feature** to make tests pass

3. **Refactor** while keeping tests green

### Mocking Strategy

For E2E tests, mock external services:

```python
from unittest.mock import patch

@patch("app.agent_endpoint.TOOL_DISPATCH")
def test_with_mocked_tools(mock_dispatch):
    # Mock tool dispatch to capture calls
    mock_dispatch["save_headline"] = lambda x: "Saved"
    # Test conversation flow
```

## 📊 Monitoring and Debugging

### Structured Logging

Use structured logging for debugging:

```python
import structlog

log = structlog.get_logger("component_name")

# Log with structured data
log.info("event_name", 
         user_id=user_id,
         action="action_taken",
         duration_ms=elapsed_time)
```

### Performance Monitoring

Track key metrics:

```python
import time

start_time = time.time()
# Process request
duration = time.time() - start_time

log.info("request_processed",
         endpoint="/agent",
         duration_ms=duration * 1000,
         tool_calls=len(tool_calls))
```

### Error Handling

Implement graceful error handling:

```python
try:
    # Risky operation
    result = process_request(data)
except ValidationError as e:
    log.warning("validation_error", error=str(e), data=data)
    return error_response("Invalid input")
except Exception as e:
    log.error("unexpected_error", error=str(e), exc_info=True)
    return error_response("Temporary error, please try again")
```

## 🚀 Deployment

### Pre-deployment Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code quality checks pass: `ruff check app tests`
- [ ] No secrets in repository: `grep -r "sk-" . --exclude-dir=.git --exclude-dir=env`
- [ ] Security review completed
- [ ] Performance testing completed
- [ ] Monitoring and alerting configured

### Environment Configuration

Production environment variables:

```bash
# Required
OPENAI_API_KEY=sk-your-production-key
TWILIO_AUTH_TOKEN=your-production-token

# Optional
DEFAULT_SESSION_ID=1
ADV_VALIDATION=true
LOG_LEVEL=INFO
```

### Database Migrations

When updating database schema:

1. **Create migration script** in `migrations/`
2. **Test migration** on staging data
3. **Apply migration** during deployment
4. **Verify data integrity** post-deployment

## 🤝 Collaboration

### Git Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Make changes with atomic commits
git add specific_files
git commit -m "feat: add specific functionality"

# Push and create PR
git push -u origin feat/your-feature-name
```

### Code Review Guidelines

- **Security**: Review all changes to authentication, validation, and secrets handling
- **Testing**: Ensure adequate test coverage for new features
- **Performance**: Consider impact on response times and resource usage
- **Documentation**: Update relevant documentation for API changes

### Conventional Commits

Use conventional commit format:

- `feat:` - New features
- `fix:` - Bug fixes  
- `security:` - Security improvements
- `docs:` - Documentation updates
- `test:` - Test additions/improvements
- `refactor:` - Code refactoring
- `style:` - Code formatting

This guide ensures consistent, secure, and maintainable development practices for the WhatsPR project.