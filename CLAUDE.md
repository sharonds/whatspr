# AI Agent Instructions

This document provides essential context for AI agents working on this codebase.

## Project Overview

This is a FastAPI chatbot for WhatsApp using Twilio. The application integrates WhatsApp messaging capabilities with AI-powered responses through the Twilio API.

## Current Development Status

✅ **Phase 3: Testing & Validation COMPLETED**

Successfully completed comprehensive testing and validation of session cleanup and timeout centralization systems:
- Fixed timeout integration issues in agent_endpoint.py
- All 60 core tests passing with performance validation
- Session cleanup, timeout centralization, and rate limiting fully validated
- Backward compatibility and migration testing confirmed
- System ready for Phase 4: Documentation & Deployment

## Technology Stack

- **Language**: Python
- **Testing Framework**: Pytest
- **Web Framework**: FastAPI
- **Messaging Service**: Twilio (WhatsApp integration)

## Development Guidelines

**IMPORTANT**: Always create a plan before writing code. This ensures:
- Clear understanding of requirements
- Structured approach to implementation
- Better code organization
- Easier debugging and maintenance

When working on this project, break down tasks into manageable steps and outline your approach before beginning implementation.

## Code Quality Standards

**Documentation Requirements**: All functions and classes MUST include Google-style docstrings. This is automatically enforced through:
- `pydocstyle` linting in CI/CD pipeline
- Pre-commit hooks for immediate feedback
- Local quality checks via `./scripts/lint.sh`

**Quality Commands**:
- `./scripts/lint.sh` - Run complete quality check locally
- `pydocstyle app/ --convention=google` - Check docstring compliance
- `pre-commit run --all-files` - Run all pre-commit hooks

See `docs/DOCUMENTATION_GUIDELINES.md` for detailed docstring standards.

## OpenAI API Connection Fix

**Critical Issue Resolved**: Fixed 50% failure rate caused by empty API key during module import.

### Problem
The OpenAI client was initialized at module import time (`app/agent_runtime.py`), before environment variables were loaded. This caused the client to be created with an empty API key, leading to authentication failures.

### Solution: Lazy Initialization Pattern
Implemented `get_client()` function that creates the OpenAI client only when first accessed:

```python
# Lazy initialization to ensure env vars are loaded
_client = None

def get_client():
    """Get or create OpenAI client with proper API key."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            # Try loading from .env if not in environment
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("OPENAI_API_KEY", "")
        _client = OpenAI(api_key=api_key)
    return _client
```

### Diagnostic Tools
When encountering similar issues, use these tools:

- **Quick Diagnosis**: `python test_diagnose.py` - Comprehensive diagnostic script
- **Reliability Testing**: `pytest tests/test_reliability.py -v` - Full reliability test suite
- **Environment Check**: Verify `OPENAI_API_KEY` is set before module import

### Key Learnings
1. **Import Timing Matters**: API clients should not be initialized at module import
2. **Environment Variable Loading**: Use lazy initialization when .env loading is required
3. **Assistant Cache**: Remove `.assistant_id` files to force recreation if needed
4. **Tool Mapping**: Enhanced assistant prompt with explicit tool usage instructions

This pattern prevents module import timing issues and ensures proper API key availability.

## Rate Limiting for API Tests

**Feature Implemented**: Added comprehensive rate limiting to all API test files to prevent quota exhaustion and improve test reliability.

### Problem Solved
Tests were occasionally failing due to hitting API rate limits, particularly OpenAI and Twilio quotas during automated testing and development.

### Solution: Token Bucket Algorithm
Implemented thread-safe rate limiting with configurable rates per service:

```python
# Service-specific rate limits
OPENAI = {"calls_per_second": 0.5, "burst_size": 3}    # Conservative for OpenAI
TWILIO = {"calls_per_second": 2.0, "burst_size": 10}   # More lenient for Twilio
DEFAULT = {"calls_per_second": 1.0, "burst_size": 5}   # General purpose
```

### Key Components
- **Rate Limiter Module**: `tests/utils/rate_limiter.py` with thread-safe token bucket implementation
- **Decorators**: `@rate_limit_test` for easy test decoration
- **Base Class**: `RateLimitedTestCase` for automatic rate limiting
- **Service Configs**: Pre-configured limits for OpenAI, Twilio, and default services

### Files With Rate Limiting Applied
- All E2E test files (`tests/e2e/*.py`)
- Reliability test suite (`tests/test_reliability.py`)
- WhatsApp simulator (`tests/utils/sim_client.py`)
- Rate limiting tests (`tests/test_rate_limiting.py`)

### Usage Pattern
```python
class TestAPI(RateLimitedTestCase):
    CALLS_PER_SECOND = 0.3
    
    def test_function(self):
        response = self.make_api_call(lambda: client.request())
```

### Benefits
1. **Test Reliability**: Prevents API quota failures during test execution
2. **Cost Control**: Reduces unnecessary API usage during development
3. **Staging Safety**: Protects against overwhelming production APIs
4. **Thread Safety**: Supports concurrent test execution without race conditions

This implementation ensures consistent test execution while protecting API quotas and improving overall development workflow reliability.

## Timeout Centralization Integration for Agent Endpoint

**Feature Completed**: Successfully integrated centralized timeout management in `app/agent_endpoint.py` to complete Phase 2 infrastructure and enable Phase 3 validation.

### Problem Solved
The agent endpoint module used hardcoded timeout values, preventing centralized configuration management and causing test failures in timeout integration tests.

### Solution: Centralized Timeout Configuration
Replaced hardcoded constants with centralized timeout configuration access:

```python
# Before: Hardcoded values
MAX_AI_PROCESSING_TIME = 25.0
MAX_RETRIES = 1
RETRY_BASE_DELAY = 0.5
RETRY_MAX_DELAY = 2.0

# After: Centralized configuration
from .timeout_config import timeout_manager

def get_max_ai_processing_time() -> float:
    return timeout_manager.config.ai_processing_timeout

def get_max_retries() -> int:
    return timeout_manager.config.retry_max_attempts
```

### Key Integration Points
- **Import Integration**: Added `timeout_manager` import from `timeout_config` module
- **Backward Compatibility**: Maintained existing API through getter functions
- **Dynamic Configuration**: All timeout values now use centralized config
- **Test Validation**: Fixed 2 failing timeout integration tests

### Files Modified
- `app/agent_endpoint.py`: Integrated centralized timeout management
- All retry logic now uses `timeout_manager.config` for consistency

### Benefits
1. **Configuration Consistency**: All modules use same timeout configuration
2. **Dynamic Updates**: Timeout values can be updated without code changes
3. **Environment Profiles**: Different timeouts for dev/staging/prod environments
4. **Test Integration**: Enables comprehensive timeout testing and validation

This integration completes the Phase 2 infrastructure requirements and enables full Phase 3 testing and validation capabilities.