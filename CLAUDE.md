# AI Agent Instructions

This document provides essential context for AI agents working on this codebase.

## Project Overview

This is a FastAPI chatbot for WhatsApp using Twilio. The application integrates WhatsApp messaging capabilities with AI-powered responses through the Twilio API.

## Current Development Goal

The current goal is to test a refactored AI agent that is goal-oriented. This involves validating the agent's ability to understand user intents, maintain conversation context, and achieve specific objectives through structured interactions.

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