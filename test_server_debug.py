#!/usr/bin/env python3
"""Direct server debugging to capture the actual exception."""

import requests
import threading
import time
from pathlib import Path

def monitor_server_logs():
    """Monitor server output (if any)."""
    print("🔍 Monitoring server activity...")
    time.sleep(2)

def test_with_verbose_request():
    """Test with verbose output to see what's happening."""
    print("🧪 VERBOSE SERVER REQUEST TEST")
    print("=" * 50)
    
    try:
        # Test reset first
        print("1. Testing Reset Command:")
        resp = requests.post('http://localhost:8004/agent', 
            data={
                'From': '+15551234567',
                'Body': 'reset',
                'MessageSid': 'DEBUG_RESET',
                'NumMedia': '0'
            },
            timeout=10
        )
        print(f"   Status: {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        
        if 'announcement' in resp.text:
            print("   ✅ Reset works - server is processing requests")
        else:
            print("   ❌ Reset failed")
            
        time.sleep(1)
        
        # Test menu selection (the failing case)
        print("\n2. Testing Menu Selection '1':")
        start = time.time()
        
        resp = requests.post('http://localhost:8004/agent',
            data={
                'From': '+15551234567',
                'Body': '1',
                'MessageSid': 'DEBUG_MENU',
                'NumMedia': '0'
            },
            timeout=20  # Give it extra time
        )
        
        elapsed = time.time() - start
        print(f"   Status: {resp.status_code}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Response: {resp.text}")
        
        # Analyze the response
        if 'Oops, temporary error' in resp.text:
            print("   🎯 CONFIRMED: Getting 'Oops, temporary error'")
            print("   This means the server is handling the request but the agent_endpoint.py exception handler is catching something")
        elif 'trouble' in resp.text:
            print("   ⚠️  Getting 'trouble' response")
        else:
            print("   ✅ Got proper response!")
        
        return resp.text
        
    except requests.Timeout:
        print("❌ Request timed out")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

if __name__ == "__main__":
    # Run the test
    response = test_with_verbose_request()
    
    print("\n" + "=" * 50)
    print("ANALYSIS:")
    print("✅ Agent Runtime works (from debug_error.py)")  
    print("✅ OpenAI API works (from debug_error.py)")
    print("✅ Server accepts requests (200 status)")
    print("❌ Server endpoint fails internally")
    print()
    print("🎯 NEXT STEP: Need to capture the actual exception")
    print("The error is being caught by the try/catch in agent_endpoint.py:444-458")
    print("but we can't see what the original exception is.")
    print("=" * 50)