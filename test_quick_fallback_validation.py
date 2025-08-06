#!/usr/bin/env python3
"""
Quick Timeout Fallback Validation - Phase 2 Optimization Impact

Quick validation of Phase 2 optimizations with 5 representative test cases.
Focus: Measure if fallback rate dropped from ~20% to <5%.
"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load optimized configuration
load_dotenv('.env.timeout-optimized')


def test_timeout_fallback_rate():
    """Quick test of timeout fallback rate with optimized configuration."""
    print("🚀 QUICK TIMEOUT FALLBACK VALIDATION")
    print("=" * 50)

    # Load optimized config
    try:
        from app.timeout_config import timeout_manager

        config = timeout_manager.config
        print(
            f"Optimized Config: {config.ai_processing_timeout}s total, {config.ai_processing_timeout/(config.retry_max_attempts+1):.1f}s per-attempt"
        )
        print(f"Polling: base={config.polling_base_delay}s, max={config.polling_max_delay}s")
        print()

    except Exception as e:
        print(f"❌ Config error: {e}")
        return

    # Representative test cases (quick to avoid timeout)
    test_cases = [
        {"msg": "hello", "type": "simple"},
        {"msg": "1", "type": "menu"},
        {"msg": "I want to announce funding", "type": "medium"},
        {"msg": "Our Series A round of $5M", "type": "complex"},
        {"msg": "reset", "type": "command"},
    ]

    results = []

    for i, case in enumerate(test_cases, 1):
        print(f"Test {i}/5: {case['type']} - '{case['msg']}'")

        start_time = time.time()

        try:
            from app.agent_runtime import run_thread

            reply, thread_id, tool_calls = run_thread(None, case['msg'])
            elapsed = time.time() - start_time

            # Check for fallback indicators
            is_fallback = any(
                phrase in reply.lower()
                for phrase in [
                    'processing your request',
                    'try again',
                    'temporary error',
                    'give me a moment',
                ]
            )

            is_timeout = elapsed >= config.ai_processing_timeout

            results.append(
                {
                    'case': case,
                    'success': not is_fallback,
                    'is_fallback': is_fallback,
                    'is_timeout': is_timeout,
                    'time': elapsed,
                    'reply': reply[:50] + '...' if len(reply) > 50 else reply,
                }
            )

            status = "⚠️ FALLBACK" if is_fallback else "✅ SUCCESS"
            print(f"   {status} - {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.time() - start_time
            results.append(
                {
                    'case': case,
                    'success': False,
                    'is_fallback': True,
                    'is_timeout': elapsed >= config.ai_processing_timeout,
                    'time': elapsed,
                    'error': str(e),
                }
            )
            print(f"   ❌ ERROR - {elapsed:.2f}s: {str(e)[:30]}...")

        # Small delay between tests
        if i < len(test_cases):
            time.sleep(0.5)

    # Analysis
    print()
    print("📊 RESULTS ANALYSIS")
    print("=" * 30)

    total_tests = len(results)
    fallback_count = len([r for r in results if r['is_fallback']])
    success_count = len([r for r in results if r['success']])

    fallback_rate = (fallback_count / total_tests) * 100
    success_rate = (success_count / total_tests) * 100

    print(f"Total Tests: {total_tests}")
    print(f"Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
    print(f"Fallback Rate: {fallback_rate:.1f}% ({fallback_count}/{total_tests})")
    print()

    # Average response time
    response_times = [r['time'] for r in results if 'time' in r]
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        print(f"Average Response Time: {avg_time:.2f}s")
        print(f"Timeout Threshold: {config.ai_processing_timeout}s")
        print()

    # Optimization assessment
    print("🎯 OPTIMIZATION ASSESSMENT")
    print("=" * 30)

    if fallback_rate < 5.0:
        print(f"✅ SUCCESS: Fallback rate {fallback_rate:.1f}% is below 5% target")
        print("✅ Phase 2 optimizations (Task 2.1 + 2.5) are EFFECTIVE")

        improvement_estimate = 20.0 - fallback_rate  # Assuming 20% baseline
        print(f"✅ Estimated improvement: {improvement_estimate:.1f} percentage points")

    elif fallback_rate < 10.0:
        print(
            f"⚠️  PARTIAL SUCCESS: Fallback rate {fallback_rate:.1f}% improved but above 5% target"
        )
        print("⚠️  Phase 2 optimizations helping, may need Task 2.2-2.4")

    else:
        print(f"❌ NEEDS WORK: Fallback rate {fallback_rate:.1f}% still high")
        print("❌ Additional optimizations required")

    print()

    # Detailed breakdown
    print("📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        case_type = result['case']['type']
        time_taken = result.get('time', 0)
        status = (
            "SUCCESS" if result['success'] else "FALLBACK" if result['is_fallback'] else "ERROR"
        )
        print(f"   Test {i} ({case_type}): {status} - {time_taken:.2f}s")

    return fallback_rate < 5.0


if __name__ == "__main__":
    success = test_timeout_fallback_rate()

    print("=" * 50)
    if success:
        print("🎉 PHASE 2 OPTIMIZATIONS VALIDATED!")
    else:
        print("⚠️  PHASE 2 OPTIMIZATIONS NEED REFINEMENT")
    print("=" * 50)
