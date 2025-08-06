#!/usr/bin/env python3
"""Force reload of timeout configuration to pick up new environment values."""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

def force_config_reload():
    """Force timeout manager to reload configuration from environment."""
    print("🔄 FORCING TIMEOUT CONFIG RELOAD")
    print("=" * 50)
    
    try:
        from app.timeout_config import timeout_manager, TimeoutConfig
        
        print("Before reload:")
        current = timeout_manager.config
        print(f"  AI Processing Timeout: {current.ai_processing_timeout}s")
        print(f"  OpenAI Request Timeout: {current.openai_request_timeout}s")
        print(f"  Retry Max Attempts: {current.retry_max_attempts}")
        
        print(f"\nEnvironment variables:")
        print(f"  AI_PROCESSING_TIMEOUT: {os.getenv('AI_PROCESSING_TIMEOUT')}")
        print(f"  OPENAI_REQUEST_TIMEOUT: {os.getenv('OPENAI_REQUEST_TIMEOUT')}")
        print(f"  RETRY_MAX_ATTEMPTS: {os.getenv('RETRY_MAX_ATTEMPTS')}")
        
        # Force reload from environment
        print(f"\n🔧 Forcing reload from environment...")
        timeout_manager.reload_from_env()
        
        print("After reload:")
        updated = timeout_manager.config
        print(f"  AI Processing Timeout: {updated.ai_processing_timeout}s")
        print(f"  OpenAI Request Timeout: {updated.openai_request_timeout}s")
        print(f"  Retry Max Attempts: {updated.retry_max_attempts}")
        print(f"  Per-attempt timeout: {updated.ai_processing_timeout / (updated.retry_max_attempts + 1):.1f}s")
        
        # Check if it worked
        expected_ai = 25.0
        if updated.ai_processing_timeout == expected_ai:
            print(f"\n✅ SUCCESS! Configuration reloaded correctly")
            return True
        else:
            print(f"\n❌ FAILED! Expected {expected_ai}s, got {updated.ai_processing_timeout}s")
            return False
            
    except Exception as e:
        print(f"❌ Error forcing reload: {e}")
        return False

def test_server_after_reload():
    """Test server behavior after config reload."""
    print(f"\n🧪 TESTING SERVER AFTER RELOAD")
    print("=" * 50)
    
    try:
        import requests
        import time
        
        # Test reset first
        resp = requests.post('http://localhost:8004/agent', 
            data={
                'From': '+15551234567',
                'Body': 'reset',
                'MessageSid': 'RELOAD_TEST_1',
                'NumMedia': '0'
            },
            timeout=5
        )
        
        if resp.status_code != 200 or 'announcement' not in resp.text:
            print("❌ Server not responding correctly to reset")
            return False
        
        print("✅ Server responding to reset")
        
        # Test menu selection (the problematic one)
        print("Testing menu selection '1'...")
        start = time.time()
        
        resp = requests.post('http://localhost:8004/agent',
            data={
                'From': '+15551234567',
                'Body': '1',
                'MessageSid': 'RELOAD_TEST_2',
                'NumMedia': '0'
            },
            timeout=30  # Give it extra time with new config
        )
        
        elapsed = time.time() - start
        print(f"Response time: {elapsed:.2f}s")
        
        if 'Oops, temporary error' in resp.text:
            print("❌ Still getting 'Oops, temporary error'")
            return False
        elif 'company name' in resp.text.lower() or 'ready' in resp.text.lower():
            print("✅ SUCCESS! Got proper AI response")
            print(f"Response: {resp.text[:200]}...")
            return True
        else:
            print(f"❓ Unexpected response: {resp.text[:200]}...")
            return False
            
    except requests.Timeout:
        print("❌ Request still timing out")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    # Force config reload
    reload_success = force_config_reload()
    
    if reload_success:
        print("\nWaiting 3 seconds for changes to take effect...")
        import time
        time.sleep(3)
        
        # Test server behavior
        server_success = test_server_after_reload()
        
        print("\n" + "=" * 50)
        print("FINAL RESULTS:")
        print(f"  Config Reload: {'✅' if reload_success else '❌'}")
        print(f"  Server Test: {'✅' if server_success else '❌'}")
        
        if reload_success and server_success:
            print("\n🎉 SUCCESS! The timeout configuration issue is fixed!")
        elif reload_success:
            print("\n⚠️  Config reloaded but server still has issues")
        else:
            print("\n❌ Could not reload configuration")
    else:
        print("\n❌ Failed to reload configuration")
        
    print("=" * 50)