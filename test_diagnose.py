#!/usr/bin/env python3
"""Quick diagnostic script to identify 50% failure rate issue in WhatsApp bot.

Run this directly to get immediate insights into the failure pattern.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Setup environment
os.environ.setdefault('TWILIO_AUTH_TOKEN', 'test-token')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent_runtime import create_thread, run_thread, get_assistant_id
from openai import OpenAI
from tests.utils.sim_client import WhatsSim


def colored_print(message, color="reset"):
    """Print with color for better visibility."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


def test_openai_connection():
    """Test 1: Direct OpenAI API connection."""
    colored_print("\n🔍 TEST 1: OpenAI API Connection", "blue")

    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

        # Test API key validity
        client.models.list()
        colored_print("  ✅ API Key is valid", "green")

        # Test assistant access
        assistant = client.beta.assistants.retrieve(get_assistant_id())
        colored_print(f"  ✅ Assistant accessible: {assistant.id}", "green")
        colored_print(f"     Model: {assistant.model}", "green")
        colored_print(f"     Tools: {len(assistant.tools) if assistant.tools else 0}", "green")

        return True
    except Exception as e:
        colored_print(f"  ❌ OpenAI API Error: {e}", "red")
        return False


def test_thread_management():
    """Test 2: Thread creation and management."""
    colored_print("\n🔍 TEST 2: Thread Management", "blue")

    results = {"success": 0, "failure": 0, "times": []}

    for i in range(5):
        start = time.time()
        try:
            thread_id = create_thread()
            elapsed = time.time() - start
            results["success"] += 1
            results["times"].append(elapsed)
            colored_print(f"  ✅ Thread {i+1}: {thread_id} ({elapsed:.2f}s)", "green")
        except Exception as e:
            results["failure"] += 1
            colored_print(f"  ❌ Thread {i+1} failed: {e}", "red")

        time.sleep(0.5)  # Avoid rate limiting

    if results["times"]:
        avg_time = sum(results["times"]) / len(results["times"])
        colored_print(f"\n  📊 Success rate: {results['success']}/5", "yellow")
        colored_print(f"  📊 Avg creation time: {avg_time:.2f}s", "yellow")

    return results["success"] >= 3


def test_message_processing():
    """Test 3: Message processing with tool calls."""
    colored_print("\n🔍 TEST 3: Message Processing & Tool Calls", "blue")

    try:
        thread_id = create_thread()

        test_messages = [
            ("Hi, I need help with a press release", "greeting"),
            ("I want to announce a funding round", "intent"),
            ("My company TechCorp raised $5 million", "data_with_tools"),
        ]

        for message, msg_type in test_messages:
            colored_print(f"\n  Testing: {msg_type}", "yellow")
            colored_print(f"  Message: '{message}'", "yellow")

            start = time.time()
            reply, _, tool_calls = run_thread(thread_id, message)
            elapsed = time.time() - start

            colored_print(f"  Response time: {elapsed:.2f}s", "green")
            colored_print(f"  Tool calls: {len(tool_calls)}", "green")
            colored_print(f"  Reply preview: {reply[:100]}...", "green")

            if tool_calls:
                for tool in tool_calls:
                    colored_print(f"    - {tool.get('name')}: {tool.get('arguments')}", "blue")

            time.sleep(1)

        return True
    except Exception as e:
        colored_print(f"  ❌ Message processing failed: {e}", "red")
        return False


def test_concurrent_load():
    """Test 4: Concurrent session handling."""
    colored_print("\n🔍 TEST 4: Concurrent Sessions", "blue")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def run_session(session_id):
        try:
            bot = WhatsSim(phone=f"+1555000{1000 + session_id}")
            bot.send("reset")
            response = bot.send("1")  # Funding

            if response and "oops" not in response.lower():
                return {"id": session_id, "success": True}
            else:
                return {"id": session_id, "success": False, "response": response[:50]}
        except Exception as e:
            return {"id": session_id, "success": False, "error": str(e)}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_session, i) for i in range(3)]
        results = [f.result() for f in as_completed(futures)]

    success_count = sum(1 for r in results if r["success"])

    for result in results:
        if result["success"]:
            colored_print(f"  ✅ Session {result['id']}: SUCCESS", "green")
        else:
            error_msg = result.get("error", result.get("response", "Unknown"))
            colored_print(f"  ❌ Session {result['id']}: FAILED - {error_msg}", "red")

    colored_print(f"\n  📊 Concurrent success rate: {success_count}/3", "yellow")

    return success_count >= 2


def test_failure_patterns():
    """Test 5: Identify failure patterns."""
    colored_print("\n🔍 TEST 5: Failure Pattern Analysis", "blue")

    bot = WhatsSim()
    patterns = {"empty_responses": 0, "error_messages": 0, "timeouts": 0, "successful": 0}

    test_sequence = ["reset", "1", "TechCorp", "Raised $5M", "CEO quote here"]

    for i, message in enumerate(test_sequence):
        try:
            start = time.time()
            response = bot.send(message)
            elapsed = time.time() - start

            if not response:
                patterns["empty_responses"] += 1
                colored_print(f"  ⚠️  Step {i+1}: Empty response", "yellow")
            elif "oops" in response.lower() or "error" in response.lower():
                patterns["error_messages"] += 1
                colored_print(f"  ⚠️  Step {i+1}: Error in response", "yellow")
            elif elapsed > 10:
                patterns["timeouts"] += 1
                colored_print(f"  ⚠️  Step {i+1}: Slow response ({elapsed:.2f}s)", "yellow")
            else:
                patterns["successful"] += 1
                colored_print(f"  ✅ Step {i+1}: OK ({elapsed:.2f}s)", "green")

            time.sleep(1)

        except Exception as e:
            colored_print(f"  ❌ Step {i+1}: Exception - {e}", "red")

    colored_print("\n  📊 Pattern Summary:", "yellow")
    for pattern, count in patterns.items():
        colored_print(f"     {pattern}: {count}", "yellow")

    return patterns["successful"] >= 3


def main():
    """Run all diagnostic tests."""
    colored_print("=" * 60, "blue")
    colored_print("WHATSAPP BOT 50% FAILURE DIAGNOSTIC", "blue")
    colored_print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "blue")
    colored_print("=" * 60, "blue")

    # Check environment
    api_key = os.environ.get("OPENAI_API_KEY", "")
    colored_print("\n📌 Environment:", "yellow")
    colored_print(
        f"  API Key: {'✅ Present' if api_key else '❌ Missing'}", "green" if api_key else "red"
    )
    colored_print(f"  Key length: {len(api_key)} chars", "yellow")
    colored_print(f"  Assistant ID: {get_assistant_id()}", "yellow")

    # Run tests
    tests = [
        ("OpenAI Connection", test_openai_connection),
        ("Thread Management", test_thread_management),
        ("Message Processing", test_message_processing),
        ("Concurrent Load", test_concurrent_load),
        ("Failure Patterns", test_failure_patterns),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            colored_print(f"\n❌ {test_name} crashed: {e}", "red")
            results[test_name] = False

    # Summary
    colored_print("\n" + "=" * 60, "blue")
    colored_print("DIAGNOSTIC SUMMARY", "blue")
    colored_print("=" * 60, "blue")

    pass_count = sum(1 for v in results.values() if v)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        color = "green" if passed else "red"
        colored_print(f"  {status} - {test_name}", color)

    colored_print(f"\n  Overall: {pass_count}/{len(tests)} tests passed", "yellow")

    # Recommendations
    colored_print("\n📋 RECOMMENDATIONS:", "yellow")

    if not results.get("OpenAI Connection"):
        colored_print("  1. Check OpenAI API key and quota", "red")
        colored_print("  2. Verify assistant ID is correct", "red")

    if not results.get("Thread Management"):
        colored_print("  1. Check for thread creation rate limits", "red")
        colored_print("  2. Consider implementing retry logic", "red")

    if not results.get("Message Processing"):
        colored_print("  1. Review assistant prompt for tool usage", "red")
        colored_print("  2. Check tool definitions in assistant", "red")

    if not results.get("Concurrent Load"):
        colored_print("  1. Implement session pooling", "red")
        colored_print("  2. Add request queuing", "red")

    if not results.get("Failure Patterns"):
        colored_print("  1. Add comprehensive error handling", "red")
        colored_print("  2. Implement retry with exponential backoff", "red")

    colored_print("\n" + "=" * 60, "blue")


if __name__ == "__main__":
    main()
