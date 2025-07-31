# PR #12 & #13: Agent Spike + Validator Tool

## Overview
This PR introduces an experimental agent endpoint that integrates with OpenAI's Assistants API to provide conversational AI capabilities for WhatsApp interactions, enhanced with input validation tools.

## Features Added

### 🤖 OpenAI Assistants Integration
- **Agent Module** (`app/agent.py`): Core integration with OpenAI Assistants API
  - Thread management for conversation continuity
  - Tool calling support with custom functions
  - Assistant configuration and prompt management

### 🌐 Agent Endpoint
- **Agent Endpoint** (`app/agent_endpoint.py`): FastAPI router for agent mode
  - `/agent` POST endpoint for WhatsApp messages
  - Session management with conversation threads
  - TwiML response formatting
  - Error handling and graceful fallbacks

### 🔧 Support Infrastructure
- **Setup Assistant** (`setup_assistant.py`): Script to create/configure OpenAI assistant
- **Agent App Wrapper** (`agent_app.py`): Standalone FastAPI app for testing
- **Start Script** (`start_agent.py`): Custom startup with environment loading
- **Assistant Prompt** (`prompts/assistant.txt`): WhatsPR agent prompt and instructions

### ✅ Input Validation Tool
- **Validators Module** (`app/validators.py`): Regex-based validation for money and email formats
- **Validator Tool** (`app/validator_tool.py`): Integration tool callable by OpenAI Assistants
- **YAML Configuration**: Add `validator: {type: money, max_retries: 1}` to slot specifications
- **Validation Types**: Money format (`$3.5M`, `$1,000`) and email validation
- **Test Coverage** (`tests/test_validators.py`): Comprehensive validation testing

### 🧪 Testing
- **Test Suite** (`tests/test_agent.py`): Basic test framework for agent functionality

## Technical Details

### Dependencies
- Updated `openai==1.31.0` for latest Assistants API features
- Maintains compatibility with existing FastAPI/Twilio integration

### Assistant Configuration
The agent uses a structured approach to collect press release information:
- **Slots**: announcement_type, headline, key_facts, quotes, boilerplate, media_contact
- **Tools**: save_slot(), get_slot(), finish(), validate_local()
- **Conversation Flow**: One question at a time, ≤20 words
- **Validation**: Automatic input validation with helpful error messages

### Integration Points
- Integrates with existing WhatsApp webhook infrastructure
- Uses prefilter for message processing
- Maintains TwiML response format for Twilio compatibility

## Setup Instructions

1. **Environment Setup**:
   ```bash
   # Add to .env file
   OPENAI_API_KEY=your_openai_api_key_here
   ```

2. **Create OpenAI Assistant**:
   ```bash
   python setup_assistant.py
   ```

3. **Start Agent Server**:
   ```bash
   python start_agent.py
   # or
   python agent_app.py
   ```

4. **Test Endpoint**:
   ```bash
   curl -X POST http://localhost:8000/agent \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "From=whatsapp:+1234567890&Body=Hello"
   ```

## Usage

Once configured, the agent endpoint can be used as an alternative to the standard WhatsApp flow. Messages sent to the `/agent` endpoint will be processed by the OpenAI Assistant, which will guide users through collecting press release information using structured conversations.

## Status

🚧 **Experimental Feature** - This is a spike implementation for testing conversational AI capabilities. The assistant must be created in OpenAI platform before the endpoint becomes fully functional.

## Next Steps

- Create "whatspr-agent" assistant in OpenAI platform
- Test end-to-end conversation flow
- Integrate with main WhatsApp router for production use
- Add conversation persistence and session management
