# Final Acceptance Test Plan - WhatsPR Agent

This comprehensive test plan validates the complete implementation of PR1 (Atomic Tools), PR2 (Goal-Oriented Prompt), and PR3 (File Search Knowledge) for the WhatsPR staging environment.

## Test Environment Requirements

- **Branch**: `refactor/agent-architecture` or merged staging branch
- **Port**: 8001 (staging server)
- **Environment**: `.env.staging` with staging API keys
- **Assistant**: Uses `.assistant_id.staging` 
- **Knowledge File**: `knowledge/press_release_requirements.txt`
- **Prompt**: `prompts/assistant_v2.txt`

## 1. System Health Check

Execute all pytest commands to ensure system integrity:

```bash
# 1.1 Run complete test suite
pytest tests/ -v

# 1.2 Verify atomic tools implementation (PR1)
pytest tests/test_tools_atomic.py -v

# 1.3 Verify prompt file exists (PR2)
pytest tests/test_prompt_exists.py -v

# 1.4 Verify knowledge file exists (PR3)
pytest tests/test_knowledge_exists.py -v

# 1.5 Safety check - no production keys in staging
pytest tests/test_safety.py -v

# 1.6 Verify tool registration
python -c "
from app.agent_runtime import ATOMIC_FUNCS
from app.agent_endpoint import TOOL_DISPATCH
print(f'✅ Atomic tools registered: {len([f for f in ATOMIC_FUNCS if f in TOOL_DISPATCH])}/{len(ATOMIC_FUNCS)}')
print(f'✅ Tools: {ATOMIC_FUNCS}')
"

# 1.7 Verify assistant configuration
python -c "
from pathlib import Path
print(f'✅ Staging assistant exists: {Path(\".assistant_id.staging\").exists()}')
print(f'✅ V2 prompt exists: {Path(\"prompts/assistant_v2.txt\").exists()}')
print(f'✅ Knowledge file exists: {Path(\"knowledge/press_release_requirements.txt\").exists()}')
"
```

### Expected Results:
- All tests should pass (28+ tests)
- No import errors
- All 6 atomic tools registered
- All required files present

## 2. Conversational Scenarios

### 2.1 Happy Path - Complete Press Release Flow

Test the agent's ability to collect information naturally and use atomic tools correctly.

```bash
# Reset session
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=reset"

# Step 1: Initial request
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=Hi, I need to create a press release for our Series A funding"

# Step 2: Provide multiple details at once
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=We're TechCorp AI Inc. We just raised \$15M led by Venture Partners. The headline should be 'TechCorp Secures \$15M to Revolutionize AI Automation'"

# Step 3: Continue with more details
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=Our CEO Jane Smith said 'This funding will accelerate our mission to make AI accessible to every business.' The investor John Doe from Venture Partners added 'TechCorp's vision aligns perfectly with market needs.'"

# Step 4: Complete remaining information
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=TechCorp is a leading AI automation platform serving over 1000 enterprises globally. Founded in 2020, we help businesses automate complex workflows. Media contact is Sarah Johnson at sarah@techcorp.com, 555-0123"
```

**Expected Behaviors:**
- Natural, conversational responses
- Multiple atomic tool calls: `save_company_name`, `save_funding_amount`, `save_headline`, `save_spokesperson_quote`, `save_media_contact`
- No template-style responses
- Completion within 12 turns

### 2.2 Edge Case - User Questions About Requirements

Test the agent's ability to use the knowledge file (PR3) to answer questions about what information is needed.

```bash
# Reset session
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567891&Body=reset"

# Step 1: Start conversation
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567891&Body=I want to create a press release but I'm not sure what you need"

# Step 2: Ask about requirements
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567891&Body=What information do you need from me?"

# Step 3: Ask about specific requirements
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567891&Body=What format should the media contact be in?"

# Step 4: Provide partial information
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567891&Body=Our company is called InnovateTech and we're announcing a new product launch"

# Step 5: Ask what's still needed
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567891&Body=What else do you still need to complete the press release?"
```

**Expected Behaviors:**
- Agent references knowledge file content when answering questions
- Provides specific guidance based on `press_release_requirements.txt`
- Mentions format requirements (e.g., "Name • email • phone" for media contact)
- Lists remaining required information accurately

### 2.3 Edge Case - Corrections and Updates

Test the agent's ability to handle corrections to previously provided information.

```bash
# Step 1: Provide initial information
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567892&Body=Our headline is 'StartupXYZ Raises \$5M'"

# Step 2: Correct the information
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567892&Body=Actually, let me correct that. The headline should be 'StartupXYZ Secures \$7M in Seed Funding'"

# Step 3: Verify correction was saved
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567892&Body=Can you confirm what headline you have saved?"
```

**Expected Behaviors:**
- Agent acknowledges the correction
- Calls atomic tool again with updated value
- Can confirm the updated information

## 3. Consolidated Success Criteria

### ✅ PR1 - Atomic Tools Verification
- [ ] All 6 atomic `save_*` functions are registered in the assistant
- [ ] TOOL_DISPATCH includes all atomic functions
- [ ] Agent calls specific tools like `save_headline`, `save_company_name` instead of generic `save_slot`
- [ ] Tool calls appear in logs when information is provided
- [ ] Each atomic function returns appropriate confirmation

### ✅ PR2 - Goal-Oriented Conversation
- [ ] Agent uses natural, conversational language
- [ ] No rigid templates or step-by-step instructions
- [ ] Can handle multiple pieces of information in one message
- [ ] Maintains context throughout the conversation
- [ ] Completes collection within 12 assistant turns
- [ ] Asks follow-up questions naturally based on what's missing

### ✅ PR3 - Knowledge File Integration
- [ ] Agent can answer "What information do you need?"
- [ ] References specific requirements from the knowledge file
- [ ] Provides format guidance (e.g., media contact format)
- [ ] Can list what information is still needed
- [ ] Knowledge file is properly attached to the assistant

### ✅ Integration & Quality
- [ ] All pytest tests pass (28+ tests)
- [ ] Staging environment properly isolated from production
- [ ] No crashes or unhandled exceptions
- [ ] Consistent behavior across multiple conversations
- [ ] Appropriate error handling for invalid inputs

## 4. Performance Metrics

- **Response Time**: < 5 seconds per interaction
- **Tool Call Success**: 100% of provided information triggers appropriate saves
- **Conversation Efficiency**: Complete collection in ≤ 8 turns for happy path
- **Error Recovery**: Graceful handling of corrections and invalid data

## 5. Cache Verification & Latest Code Testing

To ensure we're testing the **latest code** instead of cached versions, run these commands:

### 5.1 Force Server Restart (Recommended)
```bash
# Kill any existing servers
pkill -f "uvicorn.*8001"

# Start fresh server with reload
uvicorn app.main:app --reload --port 8001
```

### 5.2 Verify Latest Code is Loaded
```bash
# Check atomic tools are using latest code
python -c "
from app.agent_runtime import ATOMIC_FUNCS
from app.agent_endpoint import TOOL_DISPATCH
from app.tools_atomic import save_headline
import inspect
from pathlib import Path

print('🔧 CODE FRESHNESS VERIFICATION:')
print(f'✅ ATOMIC_FUNCS: {ATOMIC_FUNCS}')
print(f'✅ Registered tools: {len([f for f in ATOMIC_FUNCS if f in TOOL_DISPATCH])}/{len(ATOMIC_FUNCS)}')
print(f'✅ save_headline source: {inspect.getfile(save_headline)}')

# Check file timestamps
tools_file = Path('app/tools_atomic.py')
prompt_file = Path('prompts/assistant_v2.txt')
print(f'✅ tools_atomic.py modified: {tools_file.stat().st_mtime}')
print(f'✅ assistant_v2.txt modified: {prompt_file.stat().st_mtime}')
"
```

### 5.3 Assistant Configuration Verification
```bash
# Check assistant is using latest prompt and tools
python -c "
import os
from pathlib import Path
from openai import OpenAI

if not os.environ.get('OPENAI_API_KEY'):
    print('⚠️  Set OPENAI_API_KEY first: export OPENAI_API_KEY=\"your-key\"')
    exit()

client = OpenAI()
asst_id = Path('.assistant_id.staging').read_text().strip()
asst = client.beta.assistants.retrieve(asst_id)

print('📋 ASSISTANT STATUS:')
print(f'✅ ID: {asst.id}')
print(f'✅ Name: {asst.name}')
print(f'✅ Model: {asst.model}')
print(f'✅ Tools: {[t.type for t in asst.tools]}')
print(f'✅ Created: {asst.created_at}')

# Verify prompt is up to date
v2_prompt = Path('prompts/assistant_v2.txt').read_text().strip()
if asst.instructions.strip() == v2_prompt:
    print('✅ Using latest v2 prompt')
else:
    print('⚠️  Assistant prompt may be outdated')
    print(f'  Assistant: {asst.instructions[:100]}...')
    print(f'  File: {v2_prompt[:100]}...')
"
```

### 5.4 Live Function Test
```bash
# Test atomic tools work with latest code
curl -X POST http://localhost:8001/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+TEST_CACHE&Body=Our headline is 'Test Cache Verification - $(date)'"

# Verify unique timestamp appears in logs to confirm no caching
```

### 5.5 File Search Knowledge Verification
```bash
# Check knowledge file timestamp and content
ls -la knowledge/press_release_requirements.txt
head -10 knowledge/press_release_requirements.txt

# Verify if assistant needs knowledge file re-upload
python -c "
import os
from openai import OpenAI
from pathlib import Path

if os.environ.get('OPENAI_API_KEY'):
    client = OpenAI()
    asst_id = Path('.assistant_id.staging').read_text().strip()
    asst = client.beta.assistants.retrieve(asst_id)
    
    # Check file search tool resources
    if hasattr(asst, 'tool_resources') and asst.tool_resources:
        print('✅ File Search tool resources found')
        if hasattr(asst.tool_resources, 'file_search'):
            print(f'✅ Vector stores: {asst.tool_resources.file_search.vector_store_ids}')
        else:
            print('⚠️  No file_search in tool_resources')
    else:
        print('⚠️  No tool_resources found')
else:
    print('⚠️  OPENAI_API_KEY not set')
"
```

## 6. Debugging Commands

If any tests fail, use these commands to diagnose:

```bash
# Check current assistant configuration
python -c "
from pathlib import Path
import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
asst_id = Path('.assistant_id.staging').read_text().strip()
asst = client.beta.assistants.retrieve(asst_id)
print(f'Assistant: {asst.name}')
print(f'Model: {asst.model}')
print(f'Tools: {[t.type for t in asst.tools]}')
"

# Verify knowledge file content
head -20 knowledge/press_release_requirements.txt

# Check atomic tools implementation
grep -n "save_" app/tools_atomic.py

# Verify prompt being used
head -5 prompts/assistant_v2.txt
```

## 7. Sign-off Checklist

Before marking the implementation as complete:

1. [ ] All system health checks pass
2. [ ] Happy path scenario completes successfully
3. [ ] Edge cases handled appropriately
4. [ ] All success criteria met for PR1, PR2, and PR3
5. [ ] Performance metrics within acceptable ranges
6. [ ] No regressions in existing functionality

---

**Test Execution Date**: ________________  
**Tested By**: ________________  
**Test Result**: [ ] PASS [ ] FAIL  
**Notes**: ________________