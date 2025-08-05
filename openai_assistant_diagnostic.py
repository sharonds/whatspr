#!/usr/bin/env python3
"""
OpenAI Assistant Deep Diagnostic Tool
Analyzes OpenAI Assistant API failures in detail
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def get_assistant_id():
    """Get the assistant ID from cache file"""
    cache_file = ".assistant_id.staging"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return f.read().strip()
    
    cache_file = ".assistant_id"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return f.read().strip()
    
    return None

def main():
    print("🔍 OpenAI Assistant Deep Diagnostic")
    print("=" * 50)
    
    # Initialize client
    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return
    
    # Get assistant ID
    assistant_id = get_assistant_id()
    if not assistant_id:
        print("❌ No assistant ID found in cache files")
        return
    
    print(f"🤖 Using Assistant ID: {assistant_id}")
    
    try:
        # 1. Check assistant health
        print("\n1️⃣ Testing Assistant Health:")
        assistant = client.beta.assistants.retrieve(assistant_id)
        print(f"✅ Assistant found: {assistant.name}")
        print(f"   Model: {assistant.model}")
        print(f"   Tools: {len(assistant.tools)} tools configured")
        
        # 2. Create a test thread
        print("\n2️⃣ Creating Test Thread:")
        thread = client.beta.threads.create()
        thread_id = thread.id
        print(f"✅ Thread created: {thread_id}")
        
        # 3. Test simple message
        print("\n3️⃣ Testing Simple Message Processing:")
        test_message = "Hello, can you help me with press release?"
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=test_message
        )
        print(f"✅ Message added to thread")
        
        # Create run with detailed monitoring
        print("🚀 Creating run...")
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            timeout=10
        )
        print(f"✅ Run created: {run.id}")
        print(f"   Initial status: {run.status}")
        
        # Monitor run with detailed status tracking
        print("\n4️⃣ Monitoring Run Execution:")
        start_time = time.time()
        max_wait = 30  # 30 seconds max
        check_count = 0
        
        while True:
            check_count += 1
            elapsed = time.time() - start_time
            
            if elapsed > max_wait:
                print(f"⏰ Timeout after {elapsed:.1f}s")
                break
            
            try:
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id, 
                    run_id=run.id
                )
                
                print(f"   Check {check_count}: {run.status} (elapsed: {elapsed:.1f}s)")
                
                if run.status == "completed":
                    print("✅ Run completed successfully!")
                    break
                elif run.status in {"failed", "cancelled"}:
                    print(f"❌ Run {run.status}")
                    if run.last_error:
                        print(f"   Error: {run.last_error}")
                    break
                elif run.status == "requires_action":
                    print(f"🔧 Run requires action")
                    if run.required_action:
                        tool_calls = run.required_action.submit_tool_outputs.tool_calls
                        print(f"   Tool calls required: {len(tool_calls)}")
                        for i, call in enumerate(tool_calls):
                            print(f"     {i+1}. {call.function.name}")
                    # For diagnostic purposes, just submit empty outputs
                    tool_outputs = []
                    for call in tool_calls:
                        tool_outputs.append({
                            "tool_call_id": call.id,
                            "output": json.dumps({"status": "test_diagnostic"})
                        })
                    
                    run = client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print("   Tool outputs submitted")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error checking run status: {e}")
                break
        
        # 5. Try to get response if completed
        if run.status == "completed":
            print("\n5️⃣ Retrieving Response:")
            messages = client.beta.threads.messages.list(
                thread_id=thread_id, 
                limit=5
            )
            
            assistant_messages = [m for m in messages.data if m.role == "assistant"]
            if assistant_messages:
                latest_response = assistant_messages[0]
                if latest_response.content and len(latest_response.content) > 0:
                    content = latest_response.content[0]
                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                        response_text = content.text.value
                        print(f"✅ Response received ({len(response_text)} chars)")
                        print(f"   Preview: {response_text[:100]}...")
                    else:
                        print(f"❌ No text content in response (content type: {type(content).__name__})")
                else:
                    print("❌ No content in response")
            else:
                print("❌ No assistant response found")
        
        # 6. Test failure scenario
        print("\n6️⃣ Testing Potential Failure Scenario:")
        print("Creating complex message that might trigger failures...")
        
        complex_message = """We are TechCorp, a cutting-edge AI startup based in San Francisco. 
        We just raised $15M Series A funding led by Andreessen Horowitz with participation from 
        Y Combinator, First Round Capital, and several notable angel investors including former 
        OpenAI executives. Our revolutionary AI platform processes natural language at unprecedented 
        scale and we're announcing this funding to establish market leadership in the enterprise 
        AI space. The funding will accelerate our product development, expand our engineering team, 
        and fuel our go-to-market strategy targeting Fortune 500 companies."""
        
        # Create new thread for complex test
        complex_thread = client.beta.threads.create()
        complex_thread_id = complex_thread.id
        
        message = client.beta.threads.messages.create(
            thread_id=complex_thread_id,
            role="user",
            content=complex_message
        )
        
        complex_run = client.beta.threads.runs.create(
            thread_id=complex_thread_id,
            assistant_id=assistant_id,
            timeout=10
        )
        
        print(f"✅ Complex run created: {complex_run.id}")
        
        # Monitor complex run
        start_time = time.time()
        check_count = 0
        
        while True:
            check_count += 1
            elapsed = time.time() - start_time
            
            if elapsed > 30:  # 30 second timeout
                print(f"⏰ Complex run timeout after {elapsed:.1f}s")
                break
            
            try:
                complex_run = client.beta.threads.runs.retrieve(
                    thread_id=complex_thread_id, 
                    run_id=complex_run.id
                )
                
                print(f"   Complex check {check_count}: {complex_run.status} (elapsed: {elapsed:.1f}s)")
                
                if complex_run.status == "completed":
                    print("✅ Complex run completed!")
                    break
                elif complex_run.status in {"failed", "cancelled"}:
                    print(f"❌ Complex run {complex_run.status}")
                    if complex_run.last_error:
                        print(f"   Error details: {complex_run.last_error}")
                        print(f"   Error code: {getattr(complex_run.last_error, 'code', 'N/A')}")
                        print(f"   Error message: {getattr(complex_run.last_error, 'message', 'N/A')}")
                    break
                elif complex_run.status == "requires_action":
                    if complex_run.required_action:
                        tool_calls = complex_run.required_action.submit_tool_outputs.tool_calls
                        print(f"   Tool calls: {len(tool_calls)}")
                        # Submit empty outputs for diagnostic
                        tool_outputs = []
                        for call in tool_calls:
                            tool_outputs.append({
                                "tool_call_id": call.id,
                                "output": json.dumps({"status": "diagnostic_test"})
                            })
                        
                        complex_run = client.beta.threads.runs.submit_tool_outputs(
                            thread_id=complex_thread_id,
                            run_id=complex_run.id,
                            tool_outputs=tool_outputs
                        )
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in complex run: {e}")
                print(f"   Exception type: {type(e).__name__}")
                break
        
        print("\n📊 DIAGNOSTIC SUMMARY:")
        print("=" * 50)
        if run.status == "completed":
            print("✅ Simple message: SUCCESS")
        else:
            print(f"❌ Simple message: FAILED ({run.status})")
        
        if complex_run.status == "completed":
            print("✅ Complex message: SUCCESS") 
        else:
            print(f"❌ Complex message: FAILED ({complex_run.status})")
        
        print(f"\n🔍 POTENTIAL ISSUES IDENTIFIED:")
        if complex_run.status in {"failed", "cancelled"}:
            print("   - OpenAI Assistant runs failing for complex messages")
            print("   - Possible assistant configuration issue")
            print("   - Potential model overload or context limit exceeded")
        
        print(f"\n💡 NEXT STEPS:")
        print("   1. Check assistant configuration and prompts")
        print("   2. Review OpenAI usage limits and quotas")
        print("   3. Consider implementing assistant health monitoring")
        print("   4. Add more detailed error logging in agent_runtime.py")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        print(f"   Exception type: {type(e).__name__}")

if __name__ == "__main__":
    main()
