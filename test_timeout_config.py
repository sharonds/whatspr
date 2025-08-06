#!/usr/bin/env python3
"""Test the timeout configuration to see what the server is actually using."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

def test_server_timeout_config():
    """Test what timeout configuration the server is using."""
    print("🔍 TIMEOUT CONFIGURATION TEST")
    print("=" * 50)
    
    try:
        from app.timeout_config import timeout_manager
        
        config = timeout_manager.config
        
        print("Current Timeout Configuration:")
        print(f"  AI Processing Timeout: {config.ai_processing_timeout}s")
        print(f"  OpenAI Request Timeout: {config.openai_request_timeout}s")
        print(f"  Retry Max Attempts: {config.retry_max_attempts}")
        print(f"  Per-attempt timeout: {config.ai_processing_timeout / (config.retry_max_attempts + 1):.1f}s")
        
        print(f"\nPolling Configuration:")
        print(f"  Max Attempts: {config.polling_max_attempts}")
        print(f"  Base Delay: {config.polling_base_delay}s")
        print(f"  Max Delay: {config.polling_max_delay}s")
        
        # Check if this matches our .env file
        import os
        print(f"\nEnvironment Variables:")
        print(f"  AI_PROCESSING_TIMEOUT: {os.getenv('AI_PROCESSING_TIMEOUT', 'NOT SET')}")
        print(f"  OPENAI_REQUEST_TIMEOUT: {os.getenv('OPENAI_REQUEST_TIMEOUT', 'NOT SET')}")
        print(f"  RETRY_MAX_ATTEMPTS: {os.getenv('RETRY_MAX_ATTEMPTS', 'NOT SET')}")
        
        # Test if config matches expected values
        expected_ai_timeout = 25.0
        expected_retry_attempts = 1
        
        print(f"\nConfiguration Check:")
        if config.ai_processing_timeout == expected_ai_timeout:
            print(f"  ✅ AI timeout correct: {config.ai_processing_timeout}s")
        else:
            print(f"  ❌ AI timeout wrong: expected {expected_ai_timeout}s, got {config.ai_processing_timeout}s")
            
        if config.retry_max_attempts == expected_retry_attempts:
            print(f"  ✅ Retry attempts correct: {config.retry_max_attempts}")
        else:
            print(f"  ❌ Retry attempts wrong: expected {expected_retry_attempts}, got {config.retry_max_attempts}")
        
        return config
        
    except Exception as e:
        print(f"❌ Error accessing timeout config: {e}")
        return None

def test_actual_timeout_calculation():
    """Test the actual timeout calculation used in agent_endpoint.py"""
    print("\n🧮 TIMEOUT CALCULATION TEST")
    print("=" * 50)
    
    try:
        from app.agent_endpoint import get_max_ai_processing_time, get_max_retries
        
        ai_timeout = get_max_ai_processing_time()
        max_retries = get_max_retries()
        per_attempt = ai_timeout / (max_retries + 1)
        
        print(f"Agent Endpoint Configuration:")
        print(f"  AI Processing Timeout: {ai_timeout}s")
        print(f"  Max Retries: {max_retries}")
        print(f"  Per-attempt timeout: {per_attempt:.1f}s")
        print(f"  Total attempts: {max_retries + 1}")
        
        # This should explain the 14.86s timing we saw
        print(f"\nTiming Analysis:")
        if abs(per_attempt - 14.86) < 2.0:  # Within 2 seconds
            print(f"  🎯 MATCH! The 14.86s timing matches per-attempt timeout")
            print(f"  This suggests the first attempt is timing out")
        else:
            print(f"  ❓ Timing doesn't match expected per-attempt timeout")
        
        return ai_timeout, max_retries, per_attempt
        
    except Exception as e:
        print(f"❌ Error testing timeout calculation: {e}")
        return None, None, None

if __name__ == "__main__":
    config = test_server_timeout_config()
    timeout_values = test_actual_timeout_calculation()
    
    print("\n" + "=" * 50)
    print("DIAGNOSIS:")
    
    if config and timeout_values[0]:
        ai_timeout, max_retries, per_attempt = timeout_values
        
        if per_attempt > 12.0:  # Should be enough for OpenAI
            print("✅ Per-attempt timeout looks reasonable")
            print("🎯 LIKELY ISSUE: OpenAI Assistant API call is taking too long")
            print("   - Direct agent_runtime.run_thread() works (~2-5s)")
            print("   - Server endpoint times out (~15s)")
            print("   - This suggests an environment or async issue")
        else:
            print("❌ Per-attempt timeout too short")
            
    else:
        print("❌ Could not analyze timeout configuration")
        
    print("\n🔧 NEXT INVESTIGATION:")
    print("1. Check if server environment differs from direct test environment")
    print("2. Test if async wrapper is causing the delay")
    print("3. Compare working direct call vs failing server call")
    print("=" * 50)