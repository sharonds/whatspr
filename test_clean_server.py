#!/usr/bin/env python3
"""Test script for clean server with timeout fixes."""

import requests
import time


def test_server_startup():
    """Check if server started successfully."""
    try:
        resp = requests.get('http://localhost:8004/', timeout=5)
        if resp.status_code == 200:
            print("✅ Server is responding")
            print(f"   Response: {resp.json()}")
            return True
        else:
            print(f"❌ Server error: {resp.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach server: {e}")
        return False


def test_reset_functionality():
    """Test basic reset functionality."""
    print("\n🔄 Testing Reset Functionality...")
    try:
        resp = requests.post(
            'http://localhost:8004/agent',
            data={
                'From': '+15551234567',
                'Body': 'reset',
                'MessageSid': 'CLEAN_TEST_1',
                'NumMedia': '0',
            },
            timeout=10,
        )

        if resp.status_code == 200:
            if 'announcement' in resp.text.lower():
                print("✅ Reset working - Menu displayed")
                return True
            else:
                print(f"❌ Reset returned unexpected content: {resp.text[:150]}")
                return False
        else:
            print(f"❌ Reset failed with status: {resp.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Reset request failed: {e}")
        return False


def test_menu_selection():
    """Test the critical menu selection that was failing."""
    print("\n🎯 Testing Menu Selection (Previously Failing)...")
    try:
        start_time = time.time()

        resp = requests.post(
            'http://localhost:8004/agent',
            data={
                'From': '+15551234567',
                'Body': '1',
                'MessageSid': 'CLEAN_TEST_2',
                'NumMedia': '0',
            },
            timeout=15,  # Give it 15s max
        )

        elapsed = time.time() - start_time

        print(f"⏱️  Response time: {elapsed:.1f}s")

        if resp.status_code == 200:
            if 'trouble' in resp.text.lower():
                result = '❌ Still getting generic error'
                success = False
            elif 'processing' in resp.text.lower():
                result = '⏳ Still getting timeout message'
                success = False
            else:
                result = '🎉 SUCCESS! Got proper AI response'
                success = True

            print(f"   Result: {result}")
            print(f"   Response preview: {resp.text[:200]}...")
            return success
        else:
            print(f"❌ HTTP error: {resp.status_code}")
            return False

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"❌ Request timed out after {elapsed:.1f}s")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def test_direct_message():
    """Test direct message without menu selection."""
    print("\n💬 Testing Direct Message...")
    try:
        start_time = time.time()

        resp = requests.post(
            'http://localhost:8004/agent',
            data={
                'From': '+15552345678',
                'Body': 'We raised 250K from Elon Musk',
                'MessageSid': 'CLEAN_TEST_3',
                'NumMedia': '0',
            },
            timeout=15,
        )

        elapsed = time.time() - start_time
        print(f"⏱️  Response time: {elapsed:.1f}s")

        if resp.status_code == 200:
            if 'trouble' in resp.text.lower():
                result = '❌ Generic error'
                success = False
            elif 'processing' in resp.text.lower():
                result = '⏳ Timeout message'
                success = False
            else:
                result = '✅ Got response'
                success = True

            print(f"   Result: {result}")
            print(f"   Response preview: {resp.text[:150]}...")
            return success
        else:
            print(f"❌ HTTP error: {resp.status_code}")
            return False

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"❌ Request timed out after {elapsed:.1f}s")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Run complete test suite."""
    print("🧪 CLEAN SERVER TEST SUITE")
    print("=" * 50)
    print("Testing server after port conflict resolution...")
    print()

    # Test 1: Server startup
    if not test_server_startup():
        print("\n❌ Server not ready. Please start it with:")
        print("   uvicorn app.main:app --reload --port 8004")
        return

    # Test 2: Reset functionality
    reset_ok = test_reset_functionality()

    # Test 3: Menu selection (the critical failing case)
    menu_ok = test_menu_selection()

    # Test 4: Direct message
    direct_ok = test_direct_message()

    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST RESULTS:")
    print(f"   Server Startup: {'✅' if True else '❌'}")
    print(f"   Reset Function: {'✅' if reset_ok else '❌'}")
    print(f"   Menu Selection: {'✅' if menu_ok else '❌'}")
    print(f"   Direct Message: {'✅' if direct_ok else '❌'}")
    print()

    success_rate = sum([reset_ok, menu_ok, direct_ok]) / 3 * 100

    if success_rate >= 80:
        print(f"🎉 SUCCESS! {success_rate:.0f}% success rate")
        print("   Timeout fixes are working!")
    elif success_rate >= 50:
        print(f"⚠️  PARTIAL SUCCESS: {success_rate:.0f}% success rate")
        print("   Some improvements, but issues remain")
    else:
        print(f"❌ STILL FAILING: {success_rate:.0f}% success rate")
        print("   Need further investigation")

    print("=" * 50)


if __name__ == "__main__":
    main()
