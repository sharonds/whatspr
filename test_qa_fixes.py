#!/usr/bin/env python3
"""QA Test Suite for WhatsApp Agent Reliability Fixes.

Tests all the improvements made to resolve the "no response" issue:
1. Timeout increase (8s → 12s)
2. Thread state management fixes
3. Retry logic with exponential backoff
4. Production webhook integration
"""

import asyncio
import time
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent_endpoint import (
    run_thread_with_retry, 
    agent_hook, 
    _sessions,
    MAX_AI_PROCESSING_TIME,
    MAX_RETRIES
)
from tests.utils.sim_client import WhatsSim
import structlog

def colored_print(message, color="reset"):
    """Print with color for better visibility."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "purple": "\033[95m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


class MockRequest:
    """Mock FastAPI request for testing."""
    def __init__(self, form_data: dict):
        self._form_data = form_data
    
    async def form(self):
        from fastapi.datastructures import FormData
        return FormData(self._form_data)


async def test_timeout_improvements():
    """Test 1: Verify timeout increase from 8s to 12s."""
    colored_print("\n🧪 TEST 1: Timeout Improvements (8s → 12s)", "blue")
    
    # Verify the constant was updated
    if MAX_AI_PROCESSING_TIME == 12.0:
        colored_print("  ✅ Timeout constant updated to 12s", "green")
    else:
        colored_print(f"  ❌ Timeout still {MAX_AI_PROCESSING_TIME}s", "red")
        return False
    
    # Test with a message that should complete within 12s but might timeout at 8s
    start_time = time.time()
    try:
        reply, thread_id, tool_calls = await run_thread_with_retry(
            None, 
            "I want to announce a product launch for my AI startup",
            timeout_seconds=12.0
        )
        elapsed = time.time() - start_time
        
        colored_print(f"  ✅ Request completed in {elapsed:.2f}s", "green")
        colored_print(f"  Reply length: {len(reply)} chars", "green")
        colored_print(f"  Thread ID: {thread_id[:20]}..." if thread_id else "None", "green")
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        colored_print(f"  ❌ Failed after {elapsed:.2f}s: {e}", "red")
        return False


async def test_thread_state_management():
    """Test 2: Verify thread state fixes."""
    colored_print("\n🧪 TEST 2: Thread State Management", "blue")
    
    # Clear any existing sessions
    _sessions.clear()
    
    phone = "whatsapp:+1234567890"
    
    # Test 1: New session creates thread
    webhook_data = {
        'From': phone,
        'Body': 'Hello',
        'ProfileName': 'Test User'
    }
    
    mock_request = MockRequest(webhook_data)
    
    try:
        response = await agent_hook(mock_request)
        
        # Check if thread was created and stored
        if phone in _sessions and _sessions[phone]:
            colored_print(f"  ✅ Thread created: {_sessions[phone][:20]}...", "green")
        else:
            colored_print("  ❌ No thread created for new session", "red")
            return False
        
        # Test 2: Subsequent message uses same thread
        webhook_data['Body'] = 'Tell me about funding'
        mock_request2 = MockRequest(webhook_data)
        
        original_thread = _sessions[phone]
        response2 = await agent_hook(mock_request2)
        
        if _sessions[phone] == original_thread:
            colored_print("  ✅ Thread continuity maintained", "green")
        else:
            colored_print("  ❌ Thread continuity broken", "red")
            return False
        
        # Test 3: Reset command clears session
        webhook_data['Body'] = 'reset'
        mock_request3 = MockRequest(webhook_data)
        response3 = await agent_hook(mock_request3)
        
        if _sessions[phone] is None:
            colored_print("  ✅ Reset command cleared session", "green")
            return True
        else:
            colored_print("  ❌ Reset command failed to clear session", "red")
            return False
            
    except Exception as e:
        colored_print(f"  ❌ Thread state test failed: {e}", "red")
        return False


async def test_retry_logic():
    """Test 3: Verify retry logic implementation."""
    colored_print("\n🧪 TEST 3: Retry Logic with Failure Scenarios", "blue")
    
    # Test retry configuration
    colored_print(f"  📊 Max retries configured: {MAX_RETRIES}", "yellow")
    
    # Test 1: Mock a function that fails first 2 attempts, succeeds on 3rd
    attempt_count = 0
    
    async def mock_failing_run_thread(thread_id, user_msg):
        nonlocal attempt_count
        attempt_count += 1
        
        if attempt_count <= 2:
            # Simulate transient failures
            if attempt_count == 1:
                raise Exception("Simulated API rate limit")
            else:
                raise asyncio.TimeoutError("Simulated timeout")
        else:
            # Success on 3rd attempt
            return "Success after retries!", "thread_123", []
    
    # Patch the run_thread function
    with patch('app.agent_endpoint.run_thread', side_effect=mock_failing_run_thread):
        try:
            reply, thread_id, tool_calls = await run_thread_with_retry(
                None, 
                "Test retry logic",
                timeout_seconds=10.0
            )
            
            if attempt_count == 3 and "Success after retries" in reply:
                colored_print(f"  ✅ Retry logic worked: {attempt_count} attempts", "green")
                return True
            else:
                colored_print(f"  ❌ Unexpected result: {attempt_count} attempts", "red")
                return False
                
        except Exception as e:
            colored_print(f"  ❌ Retry test failed: {e}", "red")
            return False


async def test_production_webhook():
    """Test 4: Production webhook data integration."""
    colored_print("\n🧪 TEST 4: Production Webhook Integration", "blue")
    
    # Use the exact production data from your logs
    production_data = {
        'SmsMessageSid': 'SM7f5188c5ac4d373646e2826168d65044',
        'ProfileName': 'Sharon Sciammas',
        'MessageType': 'text',
        'WaId': '31621366440',
        'SmsStatus': 'received',
        'Body': 'Sharon Sciammas',
        'To': 'whatsapp:+14155238886',
        'From': 'whatsapp:+31621366440',
        'ApiVersion': '2010-04-01'
    }
    
    mock_request = MockRequest(production_data)
    
    try:
        start_time = time.time()
        response = await agent_hook(mock_request)
        elapsed = time.time() - start_time
        
        colored_print(f"  ✅ Production webhook processed in {elapsed:.2f}s", "green")
        colored_print(f"  Response type: {type(response)}", "green")
        
        # Test different message types
        test_messages = [
            ("menu", "Menu/reset command"),
            ("1", "Menu selection"),
            ("I want to announce a funding round", "Intent message"),
            ("TechCorp raised $5M", "Data with potential tool calls")
        ]
        
        for message, description in test_messages:
            production_data['Body'] = message
            mock_request = MockRequest(production_data)
            
            start_time = time.time()
            response = await agent_hook(mock_request)
            elapsed = time.time() - start_time
            
            colored_print(f"  ✅ {description}: {elapsed:.2f}s", "green")
        
        return True
        
    except Exception as e:
        colored_print(f"  ❌ Production webhook test failed: {e}", "red")
        import traceback
        traceback.print_exc()
        return False


async def test_reliability_improvements():
    """Test 5: Overall reliability improvements."""
    colored_print("\n🧪 TEST 5: Comprehensive Reliability Tests", "blue")
    
    success_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        try:
            bot = WhatsSim(phone=f"+1555{1000+i}")
            
            # Test conversation flow
            bot.send("reset")
            response1 = bot.send("1")  # Funding
            response2 = bot.send("TechCorp")  # Company name
            response3 = bot.send("We raised $5M Series A")  # Details
            
            if all([response1, response2, response3]):
                success_count += 1
                colored_print(f"  ✅ Session {i+1}: Success", "green")
            else:
                colored_print(f"  ❌ Session {i+1}: Failed", "red")
                
        except Exception as e:
            colored_print(f"  ❌ Session {i+1}: Exception - {str(e)[:50]}", "red")
    
    success_rate = (success_count / total_tests) * 100
    colored_print(f"  📊 Success rate: {success_count}/{total_tests} ({success_rate:.1f}%)", "yellow")
    
    # Success if > 80% (was experiencing ~50% before fixes)
    return success_rate > 80


async def test_concurrent_sessions():
    """Test 6: Concurrent session handling."""
    colored_print("\n🧪 TEST 6: Concurrent Session Handling", "blue")
    
    async def run_concurrent_session(session_id):
        try:
            phone = f"whatsapp:+1555{2000+session_id}"
            webhook_data = {
                'From': phone,
                'Body': 'reset',
                'ProfileName': f'User {session_id}'
            }
            
            # Reset
            mock_request = MockRequest(webhook_data)
            await agent_hook(mock_request)
            
            # Send message
            webhook_data['Body'] = 'I want to announce a product launch'
            mock_request = MockRequest(webhook_data)
            response = await agent_hook(mock_request)
            
            return {"id": session_id, "success": bool(response)}
            
        except Exception as e:
            return {"id": session_id, "success": False, "error": str(e)}
    
    # Run 5 concurrent sessions
    tasks = [run_concurrent_session(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r["success"])
    
    for result in results:
        if result["success"]:
            colored_print(f"  ✅ Concurrent session {result['id']}: Success", "green")
        else:
            error = result.get("error", "Unknown error")[:50]
            colored_print(f"  ❌ Concurrent session {result['id']}: {error}", "red")
    
    colored_print(f"  📊 Concurrent success: {success_count}/5", "yellow")
    return success_count >= 4  # Allow 1 failure


async def main():
    """Run all QA tests."""
    colored_print("="*60, "purple")
    colored_print("QA TEST SUITE - WHATSAPP AGENT RELIABILITY FIXES", "purple")
    colored_print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "purple")
    colored_print("="*60, "purple")
    
    tests = [
        ("Timeout Improvements", test_timeout_improvements),
        ("Thread State Management", test_thread_state_management),
        ("Retry Logic", test_retry_logic),
        ("Production Webhook", test_production_webhook),
        ("Reliability Improvements", test_reliability_improvements),
        ("Concurrent Sessions", test_concurrent_sessions),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            colored_print(f"\n⚡ Running: {test_name}", "blue")
            results[test_name] = await test_func()
        except Exception as e:
            colored_print(f"\n❌ {test_name} crashed: {e}", "red")
            results[test_name] = False
    
    # Summary
    colored_print("\n" + "="*60, "purple")
    colored_print("QA TEST RESULTS SUMMARY", "purple")
    colored_print("="*60, "purple")
    
    pass_count = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        color = "green" if passed else "red"
        colored_print(f"  {status} - {test_name}", color)
    
    colored_print(f"\n  📊 Overall: {pass_count}/{len(tests)} tests passed", "yellow")
    
    if pass_count == len(tests):
        colored_print("\n🎉 ALL QA TESTS PASSED! Fixes ready for production.", "green")
    elif pass_count >= len(tests) * 0.8:
        colored_print("\n⚠️  Most tests passed. Review failures before production.", "yellow")
    else:
        colored_print("\n🚨 Multiple test failures. Fixes need more work.", "red")
    
    colored_print("="*60, "purple")


if __name__ == "__main__":
    asyncio.run(main())