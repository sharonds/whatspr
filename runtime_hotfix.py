#!/usr/bin/env python3
"""Runtime hotfix to update timeout configuration without server restart."""

import requests
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


def apply_timeout_hotfix():
    """Apply timeout configuration changes at runtime."""
    try:
        # Import after path setup
        from app.timeout_config import timeout_manager, TimeoutConfig

        print("🔧 Applying Runtime Timeout Hotfix...")
        print("=" * 50)

        # Check current configuration
        current = timeout_manager.config
        print(f"Current AI Processing Timeout: {current.ai_processing_timeout}s")
        print(f"Current Retry Max Attempts: {current.retry_max_attempts}")
        print(
            f"Current Per-Attempt Timeout: {current.ai_processing_timeout / (current.retry_max_attempts + 1):.1f}s"
        )
        print()

        # Create new configuration with increased timeouts
        new_config = TimeoutConfig(
            openai_request_timeout=10.0,  # Increased from 5.0
            ai_processing_timeout=25.0,  # Increased from 15.0
            retry_max_attempts=1,  # Keep at 1 for 12.5s per attempt
            polling_max_attempts=20,  # Increased from 15
            polling_base_delay=0.5,
            polling_max_delay=4.0,
            retry_base_delay=0.5,
            retry_max_delay=2.0,
        )

        # Apply the new configuration
        timeout_manager.update_config(new_config)

        print("✅ New Configuration Applied:")
        print(f"  AI Processing Timeout: {new_config.ai_processing_timeout}s")
        print(f"  Retry Max Attempts: {new_config.retry_max_attempts}")
        print(
            f"  Per-Attempt Timeout: {new_config.ai_processing_timeout / (new_config.retry_max_attempts + 1):.1f}s"
        )
        print(f"  OpenAI Request Timeout: {new_config.openai_request_timeout}s")
        print()

        return True

    except Exception as e:
        print(f"❌ Failed to apply hotfix: {e}")
        return False


def test_hotfix_effectiveness():
    """Test if the hotfix improved performance."""
    print("🧪 Testing Hotfix Effectiveness...")
    print("=" * 50)

    try:
        import time

        # Test 1: Basic connectivity
        resp = requests.get('http://localhost:8004/', timeout=5)
        print(f"✅ Server responding: {resp.status_code}")

        # Test 2: Reset
        resp = requests.post(
            'http://localhost:8004/agent',
            data={'From': '+15551234567', 'Body': 'reset', 'MessageSid': 'HF1', 'NumMedia': '0'},
            timeout=10,
        )

        if resp.status_code == 200 and 'announcement' in resp.text:
            print("✅ Reset working")

            # Test 3: Menu selection (the critical test)
            print("🎯 Testing menu selection (previously failing)...")
            start = time.time()

            resp = requests.post(
                'http://localhost:8004/agent',
                data={'From': '+15551234567', 'Body': '1', 'MessageSid': 'HF2', 'NumMedia': '0'},
                timeout=15,
            )  # Give it 15s max

            elapsed = time.time() - start

            if 'trouble' in resp.text:
                result = '❌ Still getting error response'
                success = False
            elif 'processing' in resp.text:
                result = '⏳ Still timing out internally'
                success = False
            elif resp.status_code == 200:
                result = '✅ SUCCESS! Menu selection working'
                success = True
            else:
                result = f'❓ Unexpected status: {resp.status_code}'
                success = False

            print(f"  Result: {result}")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Response: {resp.text[:150]}...")

            return success

        else:
            print(f"❌ Reset failed: {resp.status_code}")
            return False

    except requests.Timeout:
        print("❌ Request timed out - hotfix didn't work")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 WhatsApp Bot Runtime Hotfix")
    print("=" * 50)
    print("This script applies timeout fixes without restarting the server.")
    print()

    # Apply the hotfix
    if apply_timeout_hotfix():
        print("Waiting 2 seconds for changes to take effect...")
        import time

        time.sleep(2)

        # Test effectiveness
        success = test_hotfix_effectiveness()

        print("\n" + "=" * 50)
        if success:
            print("🎉 HOTFIX SUCCESSFUL!")
            print("Menu selections should now work properly.")
        else:
            print("⚠️ HOTFIX PARTIALLY SUCCESSFUL")
            print("Configuration updated, but issues may remain.")
            print("Full server restart may still be needed.")
    else:
        print("❌ HOTFIX FAILED")
        print("Server restart is required to apply timeout fixes.")
