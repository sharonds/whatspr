#!/usr/bin/env python3
"""Quick test to verify timeout fixes are working."""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_configuration():
    """Test that configuration is loaded correctly."""
    print("🔍 Configuration Check:")
    print(f"  AI_PROCESSING_TIMEOUT: {os.getenv('AI_PROCESSING_TIMEOUT', 'NOT SET')}")
    print(f"  OPENAI_REQUEST_TIMEOUT: {os.getenv('OPENAI_REQUEST_TIMEOUT', 'NOT SET')}")
    print(f"  RETRY_MAX_ATTEMPTS: {os.getenv('RETRY_MAX_ATTEMPTS', 'NOT SET')}")
    print()


def test_menu_selection():
    """Test menu selection after reset."""
    base_url = "http://localhost:8004/agent"
    phone = "+15551234567"

    print("🧪 Testing Menu Selection Flow:")

    # Step 1: Reset
    resp = requests.post(
        base_url, data={'From': phone, 'Body': 'reset', 'MessageSid': 'SM1', 'NumMedia': '0'}
    )
    print(f"  1. Reset: {resp.status_code}")
    if "Hi! What kind of announcement?" in resp.text:
        print("     ✅ Menu displayed correctly")
    else:
        print(f"     ❌ Unexpected response: {resp.text[:100]}")

    time.sleep(1)

    # Step 2: Select option 1
    start = time.time()
    resp = requests.post(
        base_url, data={'From': phone, 'Body': '1', 'MessageSid': 'SM2', 'NumMedia': '0'}
    )
    elapsed = time.time() - start

    print(f"  2. Menu Selection '1': {resp.status_code} in {elapsed:.2f}s")

    if "I'm having trouble" in resp.text:
        print("     ❌ Still getting error response")
    elif "I'm processing" in resp.text:
        print("     ⚠️  Timeout response (needs more time)")
    else:
        print(f"     ✅ Got proper response: {resp.text[:150]}")

    return elapsed < 10 and "trouble" not in resp.text


def test_direct_message():
    """Test direct funding message."""
    base_url = "http://localhost:8004/agent"
    phone = "+15552345678"

    print("\n🧪 Testing Direct Message:")

    start = time.time()
    resp = requests.post(
        base_url,
        data={
            'From': phone,
            'Body': 'We raised 250K from Elon Musk',
            'MessageSid': 'SM3',
            'NumMedia': '0',
        },
    )
    elapsed = time.time() - start

    print(f"  Response: {resp.status_code} in {elapsed:.2f}s")

    if "I'm having trouble" in resp.text:
        print("     ❌ Error response")
    elif "I'm processing" in resp.text:
        print("     ⚠️  Timeout response")
    else:
        print(f"     ✅ Got response: {resp.text[:150]}")

    return elapsed < 10 and "trouble" not in resp.text


if __name__ == "__main__":
    print("=" * 60)
    print("TIMEOUT FIX VERIFICATION TEST")
    print("=" * 60)
    print()

    test_configuration()

    print("⚠️  NOTE: Server must be restarted to load new timeout values!")
    print("  Run: uvicorn app.main:app --reload --port 8004")
    print()

    menu_ok = test_menu_selection()
    direct_ok = test_direct_message()

    print("\n" + "=" * 60)
    print("RESULTS:")
    print(f"  Menu Selection: {'✅ PASSED' if menu_ok else '❌ FAILED'}")
    print(f"  Direct Message: {'✅ PASSED' if direct_ok else '❌ FAILED'}")

    if menu_ok and direct_ok:
        print("\n🎉 SUCCESS! Timeout fixes are working!")
    else:
        print("\n⚠️  Some tests still failing. Check server logs.")
    print("=" * 60)
