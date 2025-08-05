#!/usr/bin/env python3
"""Test script to verify the retry logic implementation."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent_endpoint import run_thread_with_retry
import structlog

# Configure basic logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.LoggerFactory(),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

async def test_retry_logic():
    """Test the retry logic with a simple message."""
    print("🧪 Testing retry logic with simple message...")
    
    try:
        # Test with a simple message that should work
        reply, thread_id, tool_calls = await run_thread_with_retry(
            None, 
            "Hello, test message", 
            timeout_seconds=6.0  # Shorter timeout to test retry behavior
        )
        
        print(f"✅ Success!")
        print(f"Reply: {reply[:100]}...")
        print(f"Thread ID: {thread_id}")
        print(f"Tool calls: {len(tool_calls)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_retry_with_existing_thread():
    """Test retry logic with an existing thread."""
    print("\n🧪 Testing retry logic with existing thread...")
    
    try:
        # First create a thread
        reply1, thread_id, _ = await run_thread_with_retry(None, "Hello", timeout_seconds=8.0)
        print(f"First message - Thread: {thread_id}")
        
        # Use the same thread for second message
        reply2, thread_id2, _ = await run_thread_with_retry(thread_id, "Tell me about funding", timeout_seconds=8.0)
        print(f"Second message - Thread: {thread_id2}")
        
        # Thread IDs should be the same
        if thread_id == thread_id2:
            print("✅ Thread continuity maintained!")
            return True
        else:
            print(f"❌ Thread continuity broken: {thread_id} != {thread_id2}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing retry logic implementation...")
    
    results = []
    results.append(asyncio.run(test_retry_logic()))
    results.append(asyncio.run(test_retry_with_existing_thread()))
    
    success_count = sum(results)
    print(f"\n📊 Results: {success_count}/{len(results)} tests passed")
    
    if success_count == len(results):
        print("🎉 All retry logic tests passed!")
    else:
        print("⚠️  Some retry logic tests failed")