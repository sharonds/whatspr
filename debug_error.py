#!/usr/bin/env python3
"""Debug script to capture server errors and identify the root cause."""

import requests
import time
import sys
import os
from pathlib import Path

# Add app to path to test imports
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if we can import key modules."""
    print("🔍 Testing Module Imports:")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("  ✅ dotenv import successful")
        
        # Test OpenAI client creation
        from app.agent_runtime import get_client
        client = get_client()
        print(f"  ✅ OpenAI client created: {type(client)}")
        
        # Test assistant access
        from app.agent_runtime import get_assistant_id
        try:
            assistant_id = get_assistant_id()
            print(f"  ✅ Assistant ID retrieved: {assistant_id[:10]}...")
        except Exception as e:
            print(f"  ❌ Assistant ID error: {e}")
        
        # Test atomic functions
        from app.agent_runtime import ATOMIC_FUNCS
        print(f"  ✅ Atomic functions loaded: {len(ATOMIC_FUNCS)} functions")
        
        # Test session manager
        from app.session_manager import SessionManager
        print("  ✅ SessionManager import successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_openai_direct():
    """Test direct OpenAI API call."""
    print("\n🤖 Testing Direct OpenAI API:")
    
    try:
        from app.agent_runtime import get_client, get_assistant_id
        
        try:
            assistant_id = get_assistant_id()
        except Exception as e:
            print(f"  ❌ Assistant ID not available: {e}")
            return False
            
        client = get_client()
        
        # Test assistant retrieval
        assistant = client.beta.assistants.retrieve(assistant_id)
        print(f"  ✅ Assistant retrieved: {assistant.name}")
        
        # Test thread creation
        thread = client.beta.threads.create()
        print(f"  ✅ Thread created: {thread.id[:10]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI API error: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False

def test_agent_runtime_direct():
    """Test agent_runtime functions directly."""
    print("\n⚙️  Testing Agent Runtime Direct:")
    
    try:
        from app.agent_runtime import run_thread
        
        print("  Testing run_thread with simple message...")
        reply, thread_id, tool_calls = run_thread(None, "Hello")
        
        print(f"  ✅ run_thread succeeded:")
        print(f"    Reply length: {len(reply)}")
        print(f"    Thread ID: {thread_id[:10]}..." if thread_id else "None")
        print(f"    Tool calls: {len(tool_calls)}")
        print(f"    Reply preview: {reply[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Agent runtime error: {e}")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error details: {str(e)}")
        return False

def test_server_request():
    """Test server request and analyze response."""
    print("\n🌐 Testing Server Request:")
    
    try:
        resp = requests.post('http://localhost:8004/agent',
            data={
                'From': '+15551234567',
                'Body': '1',  # Menu selection
                'MessageSid': 'DEBUG_TEST',
                'NumMedia': '0'
            },
            timeout=15
        )
        
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text}")
        
        if "Oops, temporary error" in resp.text:
            print("  ❌ Still getting error response")
            return False
        else:
            print("  ✅ Got proper response")
            return True
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🐛 DEBUG ERROR INVESTIGATION")
    print("=" * 50)
    
    # Check environment
    print(f"OpenAI API Key configured: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
    print()
    
    # Run tests in sequence
    import_ok = test_imports()
    if import_ok:
        openai_ok = test_openai_direct()
        if openai_ok:
            runtime_ok = test_agent_runtime_direct()
        else:
            runtime_ok = False
    else:
        openai_ok = False
        runtime_ok = False
    
    server_ok = test_server_request()
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS RESULTS:")
    print(f"  Module Imports: {'✅' if import_ok else '❌'}")
    print(f"  OpenAI API: {'✅' if openai_ok else '❌'}")
    print(f"  Agent Runtime: {'✅' if runtime_ok else '❌'}")
    print(f"  Server Request: {'✅' if server_ok else '❌'}")
    
    if not runtime_ok:
        print("\n🎯 LIKELY ISSUE: Agent Runtime Failure")
        print("The error occurs in the agent_runtime.py run_thread function")
    elif not server_ok:
        print("\n🎯 LIKELY ISSUE: Server Endpoint Error")
        print("Agent runtime works, but server endpoint fails")
    else:
        print("\n🎉 ALL TESTS PASSED - Issue may be intermittent")
    
    print("=" * 50)