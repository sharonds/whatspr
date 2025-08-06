#!/usr/bin/env python3
"""Test performance logging capabilities with sample requests."""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()


def test_agent_runtime_directly():
    """Test agent_runtime.py directly to see detailed performance logs."""
    print("🧪 TESTING AGENT RUNTIME DIRECTLY")
    print("=" * 50)

    try:
        from app.agent_runtime import run_thread

        # Test with simple message
        print("Testing with simple message: 'hello'...")
        start = time.time()

        reply, thread_id, tool_calls = run_thread(None, "hello")

        elapsed = time.time() - start
        print(f"✅ SUCCESS! Runtime test completed in {elapsed:.2f}s")
        print(f"Reply: {reply[:100]}...")
        print(f"Thread ID: {thread_id[:10]}...")
        print(f"Tool calls: {len(tool_calls)}")

        return True

    except Exception as e:
        print(f"❌ Runtime test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_timeout_configuration():
    """Check current timeout configuration."""
    print("\n🔧 CHECKING TIMEOUT CONFIGURATION")
    print("=" * 50)

    try:
        from app.timeout_config import timeout_manager

        config = timeout_manager.config
        print(f"AI Processing Timeout: {config.ai_processing_timeout}s")
        print(f"OpenAI Request Timeout: {config.openai_request_timeout}s")
        print(f"Retry Max Attempts: {config.retry_max_attempts}")
        print(
            f"Per-attempt timeout: {config.ai_processing_timeout / (config.retry_max_attempts + 1)}s"
        )

        return True

    except Exception as e:
        print(f"❌ Config check failed: {e}")
        return False


def test_performance_endpoint():
    """Test the new performance monitoring endpoint."""
    print("\n📊 TESTING PERFORMANCE ENDPOINT")
    print("=" * 50)

    try:
        import requests

        resp = requests.get('http://localhost:8004/health/performance', timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            print("✅ Performance endpoint working")
            print(f"Timeout config: {data['timeout_config']['ai_processing_timeout_ms']}ms")
            print(f"Session metrics: {data['session_metrics']}")
            print(f"Bottleneck analysis: {data['bottleneck_analysis']['primary_bottleneck']}")
            return True
        else:
            print(f"❌ Performance endpoint failed: {resp.status_code}")
            return False

    except Exception as e:
        print(f"❌ Performance endpoint test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 PERFORMANCE LOGGING VALIDATION TEST")
    print("=" * 70)

    # Run tests
    config_ok = test_timeout_configuration()
    runtime_ok = test_agent_runtime_directly()
    endpoint_ok = test_performance_endpoint()

    print("\n" + "=" * 70)
    print("VALIDATION RESULTS:")
    print(f"  Timeout Config: {'✅' if config_ok else '❌'}")
    print(f"  Agent Runtime: {'✅' if runtime_ok else '❌'}")
    print(f"  Performance Endpoint: {'✅' if endpoint_ok else '❌'}")

    if all([config_ok, runtime_ok, endpoint_ok]):
        print("\n🎉 All performance logging components working!")
        print("You should now see detailed timing logs when running requests.")
    else:
        print("\n⚠️  Some performance logging components need attention.")

    print("=" * 70)
