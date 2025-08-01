# Claude Code Test Prompt for WhatsApp PR Agent

## Context
We've implemented PR1 (Atomic Tools) and PR2 (Goal-Oriented Prompt) patches on a WhatsApp-based press release assistant. The system should now use atomic save functions instead of generic slot saving, and employ a conversational goal-oriented approach.

## Test Objectives
Please validate that our implementation is working correctly by testing:

1. **Atomic Tools Integration** - Verify the 6 atomic save functions are properly registered and functional
2. **Goal-Oriented Prompt** - Confirm the assistant uses conversational approach instead of rigid templates
3. **Tool Dispatch System** - Ensure tools are called and handled correctly
4. **Staging Environment** - Validate isolated staging setup works properly

## Current System Status

### Infrastructure
- **Branch**: `feat/atomic-tools-staging`
- **Staging Server**: Running on port 8001 with staging environment
- **ngrok Tunnel**: `https://b8e98331c90d.ngrok-free.app/agent`
- **Assistant ID**: `asst_2CdulwIHO9V4HXn6jIBIGMqM` (staging)
- **Database**: `app_staging.db` (isolated from production)

### Implemented Changes

#### PR1 - Atomic Tools
- ✅ Added `app/tools_atomic.py` with 6 atomic save functions
- ✅ Updated `app/agent_runtime.py` to register atomic tools in assistant
- ✅ Updated `app/agent_endpoint.py` dispatch table for atomic functions
- ✅ Added `tests/test_tools_atomic.py` with basic coverage
- ✅ All tests passing (26 tests total)

**Atomic Functions Available:**
- `save_announcement_type` - Announcement type (funding, product launch, etc.)
- `save_headline` - Press release headline  
- `save_key_facts` - Key facts (who, what, when, amount, investors)
- `save_quotes` - Two short quotes
- `save_boilerplate` - Company boilerplate paragraph
- `save_media_contact` - Media contact info (name, email, phone)

#### PR2 - Goal-Oriented Prompt
- ✅ Added `prompts/assistant_v2.txt` with conversational mission-style prompt
- ✅ Updated `app/agent_runtime.py` to use new v2 prompt
- ✅ Added `prompts/examples/sample_conversation.md` for reference
- ✅ Added `tests/test_prompt_exists.py` to validate prompt file

## Tests to Perform

### 1. Basic System Health Check
```bash
# Verify all tests pass
pytest tests/ -v

# Check atomic tools specifically
pytest tests/test_tools_atomic.py -v

# Verify prompt file exists
pytest tests/test_prompt_exists.py -v
```

### 2. Tool Registration Verification
```bash
# Test that atomic tools module imports correctly
python -c "import app.tools_atomic; print('✅ tools_atomic imported'); print([fn for fn in dir(app.tools_atomic) if fn.startswith('save_')])"

# Test individual atomic functions
python -c "from app.tools_atomic import save_headline; print('✅ Result:', save_headline('Test Headline'))"
```

### 3. Server Integration Test
```bash
# Test agent endpoint responds
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=Test message" | grep -o '<Message>[^<]*</Message>'
```

### 4. Tool Dispatch Validation
```bash
# Check if TOOL_DISPATCH includes atomic functions
python -c "
from app.agent_endpoint import TOOL_DISPATCH, ATOMIC_FUNCS
atomic_in_dispatch = [fn for fn in ATOMIC_FUNCS if fn in TOOL_DISPATCH]
print(f'✅ Atomic tools in dispatch: {len(atomic_in_dispatch)}/{len(ATOMIC_FUNCS)}')
print(f'Missing: {set(ATOMIC_FUNCS) - set(TOOL_DISPATCH.keys())}')
"
```

### 5. Conversation Flow Test
Test the assistant's conversational behavior by sending WhatsApp-style messages:

```bash
# Test 1: General PR request
curl -X POST https://b8e98331c90d.ngrok-free.app/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1555000001&Body=Hi, we need help with a press release"

# Test 2: Specific information provided
curl -X POST https://b8e98331c90d.ngrok-free.app/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1555000001&Body=We're TechCorp and we just raised \$10M Series A"

# Test 3: Headline specification
curl -X POST https://b8e98331c90d.ngrok-free.app/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1555000001&Body=Our headline should be: TechCorp Secures \$10M Series A to Transform AI Industry"
```

## Expected Behaviors

### ✅ Success Criteria
1. **Tools Called**: Terminal logs should show `tool_count > 0` when specific information is provided
2. **Conversational Style**: Assistant should ask natural follow-up questions, not provide templates
3. **Atomic Tool Usage**: When information is provided, assistant should call appropriate `save_*` functions
4. **Staging Isolation**: Uses `asst_2CdulwIHO9V4HXn6jIBIGMqM` assistant and `app_staging.db`
5. **Goal-Oriented Behavior**: Assistant focuses on gathering required PR information systematically

### ❌ Failure Indicators
1. **Template Responses**: Long template-style responses instead of conversational questions
2. **No Tool Calls**: `tool_count: 0` in logs when specific information is provided  
3. **Wrong Assistant**: Using old assistant ID `asst_BHEhodWiLdjtUg6bZQeQ84ZX`
4. **Test Failures**: Any pytest failures indicate integration issues
5. **Import Errors**: Unable to import `app.tools_atomic` or missing functions

## Debugging Commands

### Check Current Status
```bash
# Server status and assistant ID
curl -s http://localhost:8001/health 2>/dev/null || echo "Server not running"
cat .assistant_id.staging

# Environment validation  
python -c "
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('.env.staging')
print(f'✅ Database: {os.getenv(\"DATABASE_URL\")}')
print(f'✅ Staging file exists: {Path(\".assistant_id.staging\").exists()}')
"

# Tool integration check
python -c "
from app.agent_runtime import ATOMIC_FUNCS
from app.agent_endpoint import TOOL_DISPATCH
print(f'✅ ATOMIC_FUNCS: {ATOMIC_FUNCS}')
print(f'✅ Tools in dispatch: {[k for k in TOOL_DISPATCH.keys() if k in ATOMIC_FUNCS]}')
"
```

### Monitor Real-Time Logs
```bash
# Watch server logs for tool calls
tail -f <server_output> | grep -E "(tool_count|tool_executed|debug_response)"
```

## Files to Review
- `app/tools_atomic.py` - Atomic save functions implementation
- `app/agent_runtime.py` - Assistant creation with atomic tools
- `app/agent_endpoint.py` - Tool dispatch table with atomic functions  
- `prompts/assistant_v2.txt` - New conversational prompt
- `tests/test_tools_atomic.py` - Atomic tools test coverage
- `.assistant_id.staging` - Staging assistant ID file

## Validation Questions
1. Are all 26 tests passing including the new atomic and prompt tests?
2. Does the assistant use conversational language instead of providing templates?
3. Are atomic tools (`save_*` functions) being called when information is provided?
4. Is the staging environment properly isolated from production?
5. Does the tool dispatch system correctly route atomic tool calls?

Please run these tests and validate that our PR1 + PR2 implementation is working correctly!
