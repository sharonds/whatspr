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