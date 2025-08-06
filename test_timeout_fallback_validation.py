#!/usr/bin/env python3
"""
Timeout Fallback Rate Validation Test - Phase 2 Optimization Impact

Tests the effectiveness of our Phase 2 optimizations in reducing timeout fallback rate
from 20% to <5% by running multiple message types and measuring failure patterns.

Key Optimizations Being Tested:
1. Task 2.1: Increased per-attempt timeout from 8.3s to 15.0s (AI_PROCESSING_TIMEOUT 25s->30s, RETRY_MAX_ATTEMPTS 2->1)
2. Task 2.5: Reduced polling overhead by 52.4% (base delay 0.5s->0.2s, max delay 4.0s->2.0s)

Expected Results:
- Timeout fallback rate: <5% (down from ~20%)
- Average response time: Improved consistency
- Complex message handling: Better success rate
"""

import sys
import time
import statistics
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment with optimized settings
load_dotenv('.env.timeout-optimized')


class TimeoutFallbackValidator:
    """Comprehensive timeout fallback rate validation system."""

    def __init__(self):
        """Initialize validator with test scenarios."""
        # Test message types representing real user scenarios
        self.test_scenarios = [
            # Quick messages (should be fast)
            {"message": "hello", "type": "greeting", "expected_time": "<10s"},
            {"message": "hi", "type": "greeting", "expected_time": "<10s"},
            {"message": "1", "type": "menu_selection", "expected_time": "<12s"},
            {"message": "2", "type": "menu_selection", "expected_time": "<12s"},
            # Medium complexity (typical user input)
            {
                "message": "I want to announce our Series A funding round of $5M",
                "type": "funding_announcement",
                "expected_time": "<18s",
            },
            {
                "message": "We launched a new AI-powered analytics platform",
                "type": "product_launch",
                "expected_time": "<18s",
            },
            {
                "message": "Our company partners with Google for cloud integration",
                "type": "partnership",
                "expected_time": "<18s",
            },
            # Complex messages (historically problematic)
            {
                "message": "We've raised $10M Series A led by Andreessen Horowitz to expand our AI platform across Europe and Asia, targeting enterprise customers",
                "type": "complex_funding",
                "expected_time": "<25s",
            },
            {
                "message": "Our CEO Jane Smith said 'This funding validates our vision for democratizing AI access for small businesses worldwide'",
                "type": "complex_quote",
                "expected_time": "<25s",
            },
            {
                "message": "TechCorp Inc., founded in 2020, develops cutting-edge machine learning solutions for financial services companies",
                "type": "complex_boilerplate",
                "expected_time": "<25s",
            },
        ]

        self.results = []
        self.timeout_threshold = None

    def load_optimized_config(self):
        """Load and validate optimized timeout configuration."""
        try:
            from app.timeout_config import timeout_manager

            config = timeout_manager.config
            self.timeout_threshold = config.ai_processing_timeout

            print("📊 OPTIMIZED CONFIGURATION LOADED")
            print(f"   AI Processing Timeout: {config.ai_processing_timeout}s")
            print(f"   Retry Max Attempts: {config.retry_max_attempts}")
            print(
                f"   Per-attempt Timeout: {config.ai_processing_timeout / (config.retry_max_attempts + 1):.1f}s"
            )
            print(f"   Polling Base Delay: {config.polling_base_delay}s")
            print(f"   Polling Max Delay: {config.polling_max_delay}s")
            print()

            return True

        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False

    def run_single_test(self, scenario, test_id):
        """Run a single timeout fallback test."""
        from app.agent_runtime import run_thread

        start_time = time.time()
        message = scenario["message"]

        try:
            print(f"🧪 Test {test_id}: {scenario['type']} - '{message[:50]}...'")

            # Run the actual agent processing
            reply, thread_id, tool_calls = run_thread(None, message)

            elapsed = time.time() - start_time
            success = True
            is_fallback = "processing your request" in reply.lower() or "try again" in reply.lower()
            is_timeout = elapsed >= self.timeout_threshold

            result = {
                "test_id": test_id,
                "scenario": scenario,
                "success": success,
                "is_fallback": is_fallback,
                "is_timeout": is_timeout,
                "elapsed_time": elapsed,
                "reply_length": len(reply),
                "tool_calls": len(tool_calls),
                "reply_preview": reply[:100] + "..." if len(reply) > 100 else reply,
            }

            # Real-time feedback
            status = "✅" if success and not is_fallback else "⚠️" if is_fallback else "❌"
            print(f"   {status} {elapsed:.2f}s - {'FALLBACK' if is_fallback else 'SUCCESS'}")

            return result

        except Exception as e:
            elapsed = time.time() - start_time

            result = {
                "test_id": test_id,
                "scenario": scenario,
                "success": False,
                "is_fallback": True,
                "is_timeout": elapsed >= self.timeout_threshold,
                "elapsed_time": elapsed,
                "error": str(e),
                "error_type": type(e).__name__,
            }

            print(f"   ❌ {elapsed:.2f}s - ERROR: {str(e)[:50]}...")
            return result

    def run_sequential_tests(self):
        """Run tests sequentially to avoid API rate limiting."""
        print("🔄 RUNNING SEQUENTIAL TIMEOUT FALLBACK TESTS")
        print("=" * 60)

        for i, scenario in enumerate(self.test_scenarios, 1):
            result = self.run_single_test(scenario, i)
            self.results.append(result)

            # Brief pause between tests to avoid rate limits
            if i < len(self.test_scenarios):
                time.sleep(1)

        print()

    def analyze_results(self):
        """Analyze timeout fallback test results."""
        if not self.results:
            print("❌ No results to analyze")
            return

        # Calculate key metrics
        total_tests = len(self.results)
        successful_tests = len(
            [r for r in self.results if r["success"] and not r.get("is_fallback", False)]
        )
        fallback_tests = len([r for r in self.results if r.get("is_fallback", False)])
        timeout_tests = len([r for r in self.results if r.get("is_timeout", False)])
        error_tests = len([r for r in self.results if not r["success"]])

        # Response time analysis
        response_times = [r["elapsed_time"] for r in self.results if "elapsed_time" in r]

        fallback_rate = (fallback_tests / total_tests) * 100
        timeout_rate = (timeout_tests / total_tests) * 100
        error_rate = (error_tests / total_tests) * 100
        success_rate = (successful_tests / total_tests) * 100

        print("📊 TIMEOUT FALLBACK ANALYSIS RESULTS")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print()

        # Key Performance Metrics
        print("🎯 KEY METRICS (Target: <5% fallback rate):")
        print(f"   Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"   Fallback Rate: {fallback_rate:.1f}% ({fallback_tests}/{total_tests})")
        print(f"   Timeout Rate: {timeout_rate:.1f}% ({timeout_tests}/{total_tests})")
        print(f"   Error Rate: {error_rate:.1f}% ({error_tests}/{total_tests})")
        print()

        # Response Time Analysis
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            max_time = max(response_times)
            min_time = min(response_times)

            print("⏱️  RESPONSE TIME ANALYSIS:")
            print(f"   Average: {avg_time:.2f}s")
            print(f"   Median: {median_time:.2f}s")
            print(f"   Range: {min_time:.2f}s - {max_time:.2f}s")
            print(f"   Timeout Threshold: {self.timeout_threshold}s")
            print()

        # Scenario Performance Breakdown
        print("📋 SCENARIO PERFORMANCE:")
        scenario_stats = {}
        for result in self.results:
            scenario_type = result["scenario"]["type"]
            if scenario_type not in scenario_stats:
                scenario_stats[scenario_type] = {"total": 0, "fallbacks": 0, "times": []}

            scenario_stats[scenario_type]["total"] += 1
            if result.get("is_fallback", False):
                scenario_stats[scenario_type]["fallbacks"] += 1
            if "elapsed_time" in result:
                scenario_stats[scenario_type]["times"].append(result["elapsed_time"])

        for scenario_type, stats in scenario_stats.items():
            fallback_pct = (stats["fallbacks"] / stats["total"]) * 100
            avg_time = statistics.mean(stats["times"]) if stats["times"] else 0
            print(f"   {scenario_type}: {fallback_pct:.1f}% fallback, {avg_time:.2f}s avg")

        print()

        # Optimization Impact Assessment
        print("🔍 OPTIMIZATION IMPACT ASSESSMENT:")
        if fallback_rate < 5.0:
            print(f"   ✅ SUCCESS: Fallback rate {fallback_rate:.1f}% is below 5% target")
            print("   ✅ Task 2.1 + 2.5 optimizations are effective")
        else:
            print(f"   ⚠️  ATTENTION: Fallback rate {fallback_rate:.1f}% still above 5% target")
            print("   ⚠️  Additional optimizations may be needed")

        print()

        # Detailed Failure Analysis
        if fallback_tests > 0 or error_tests > 0:
            print("🔍 FAILURE ANALYSIS:")
            for result in self.results:
                if result.get("is_fallback", False) or not result["success"]:
                    scenario = result["scenario"]["type"]
                    time_taken = result.get("elapsed_time", 0)
                    issue = (
                        "TIMEOUT"
                        if result.get("is_timeout", False)
                        else "FALLBACK" if result.get("is_fallback", False) else "ERROR"
                    )
                    print(f"   {issue}: {scenario} - {time_taken:.2f}s")

        return {
            "fallback_rate": fallback_rate,
            "success_rate": success_rate,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "optimization_effective": fallback_rate < 5.0,
        }


def main():
    """Run comprehensive timeout fallback validation."""
    print("🚀 TIMEOUT FALLBACK RATE VALIDATION - PHASE 2 OPTIMIZATIONS")
    print("=" * 70)
    print("Testing combined impact of:")
    print("  • Task 2.1: Increased per-attempt timeout (8.3s → 15.0s)")
    print("  • Task 2.5: Reduced polling overhead (52.4% improvement)")
    print("  • Target: Reduce fallback rate from ~20% to <5%")
    print()

    validator = TimeoutFallbackValidator()

    # Load optimized configuration
    if not validator.load_optimized_config():
        print("❌ Configuration loading failed. Cannot proceed.")
        return

    # Run timeout fallback tests
    validator.run_sequential_tests()

    # Analyze results
    results_summary = validator.analyze_results()

    # Final Assessment
    print("🏁 PHASE 2 OPTIMIZATION VALIDATION COMPLETE")
    print("=" * 70)

    if results_summary and results_summary["optimization_effective"]:
        print("🎉 SUCCESS: Phase 2 optimizations are EFFECTIVE!")
        print(f"   Fallback rate: {results_summary['fallback_rate']:.1f}% (target: <5%)")
        print(f"   Success rate: {results_summary['success_rate']:.1f}%")
        print(f"   Avg response: {results_summary['avg_response_time']:.2f}s")
    else:
        print("⚠️  Phase 2 optimizations need additional work")
        print("   Consider implementing Task 2.2-2.4 for further improvement")

    print("=" * 70)


if __name__ == "__main__":
    main()
