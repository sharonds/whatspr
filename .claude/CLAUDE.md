# Claude Context for WhatsApp PR Agent

## Project Overview
WhatsApp-based press release assistant that helps users create professional press releases through conversational interface.

## Key Components
- **Agent Endpoint** (`app/agent_endpoint.py`) - Handles WhatsApp webhook requests
- **Agent Runtime** (`app/agent_runtime.py`) - OpenAI Assistant integration
- **Tools Atomic** (`app/tools_atomic.py`) - Database operations for saving PR data
- **Models** (`app/models.py`) - SQLModel database schemas

## Current Features
- Atomic tools for saving specific PR fields (headline, quotes, etc.)
- Conversational flow for gathering PR information
- Database persistence with SQLModel
- WhatsApp integration via webhook

## Development Setup
- Server runs on port 8004 (configurable in `start_agent.py`)
- Uses ngrok for webhook exposure during development
- Staging environment with separate database

## Testing
- pytest for unit tests
- Manual webhook testing with curl commands
- Integration tests for full conversation flows

## Environment
- `.env` file contains API keys and configuration
- Twilio for WhatsApp integration
- OpenAI API for conversational AI

## Architecture
- FastAPI server with webhook endpoints
- OpenAI Assistant API for conversation management
- SQLModel for database operations
- Atomic tools pattern for modular functionality

## Recent Work
- Currently on branch: feat/e2e-difficult-inputs
- Working on comprehensive E2E test suite for difficult inputs
- Server optimization and debugging for response times
