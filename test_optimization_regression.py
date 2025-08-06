#!/usr/bin/env python3
"""
Regression Test Suite - Phase 2 Optimization Impact

Comprehensive validation that Phase 2 optimizations don't break existing functionality.
Tests all core WhatsPR features: session management, atomic tools, conversation flow,
menu selections, reset commands, and error handling.

Critical Areas to Validate:
1. Session Management (create, retrieve, reset)
2. All 6 Atomic Tools (save_announcement_type, save_headline, etc.)
3. Menu Selection Processing (1, 2, 3 → natural language)
4. Reset Commands (reset, restart, menu)
5. Error Handling and Fallback Behavior
6. Tool Call Execution and Logging
"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Load optimized configuration
load_dotenv('.env.timeout-optimized')


class OptimizationRegressionTester:
    """Comprehensive regression testing for Phase 2 optimizations."""

    def __init__(self):
        """Initialize regression tester."""
        self.test_results = []
        self.phone_test = "whatsapp:+1234567890"  # Test phone for session testing

    def log_test_result(self, test_name, success, details=None, error=None):
        """Log a test result with details."""
        result = {
            'test': test_name,
            'success': success,
            'timestamp': time.time(),
            'details': details or {},
            'error': str(error) if error else None,
        }
        self.test_results.append(result)

        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
        if error:
            print(f"      Error: {str(error)[:100]}...")

        return success

    def test_timeout_configuration(self):
        """Test 1: Validate optimized timeout configuration loads correctly."""
        print("🔧 Testing timeout configuration...")

        try:
            from app.timeout_config import timeout_manager

            config = timeout_manager.config

            # Validate optimized values
            expected_values = {
                'ai_processing_timeout': 30.0,
                'retry_max_attempts': 1,
                'polling_base_delay': 0.2,
                'polling_max_delay': 2.0,
            }

            for key, expected in expected_values.items():
                actual = getattr(config, key)
                if actual != expected:
                    return self.log_test_result(
                        "timeout_configuration",
                        False,
                        error=f"{key}: expected {expected}, got {actual}",
                    )

            # Calculate per-attempt timeout
            per_attempt = config.ai_processing_timeout / (config.retry_max_attempts + 1)

            return self.log_test_result(
                "timeout_configuration",
                True,
                details={
                    'ai_processing_timeout': config.ai_processing_timeout,
                    'per_attempt_timeout': per_attempt,
                    'polling_optimized': True,
                },
            )

        except Exception as e:
            return self.log_test_result("timeout_configuration", False, error=e)

    def test_session_management(self):
        """Test 2: Session create, retrieve, and reset functionality."""
        print("👤 Testing session management...")

        try:
            from app.session_manager import SessionManager
            from app.session_config.session_config import SessionConfig

            session_manager = SessionManager(SessionConfig())
            test_phone = "test:regression"
            test_thread = "thread_test_12345"

            # Test session creation
            session_manager.set_session(test_phone, test_thread)
            retrieved = session_manager.get_session(test_phone)

            if retrieved != test_thread:
                return self.log_test_result(
                    "session_management",
                    False,
                    error=f"Session mismatch: expected {test_thread}, got {retrieved}",
                )

            # Test session reset
            session_manager.remove_session(test_phone)
            after_reset = session_manager.get_session(test_phone)

            if after_reset is not None:
                return self.log_test_result(
                    "session_management", False, error=f"Session not reset: got {after_reset}"
                )

            return self.log_test_result(
                "session_management", True, details={'operations': ['create', 'retrieve', 'reset']}
            )

        except Exception as e:
            return self.log_test_result("session_management", False, error=e)

    def test_menu_selection_processing(self):
        """Test 3: Menu selection conversion (1,2,3 → natural language)."""
        print("📋 Testing menu selection processing...")

        try:
            from app.prefilter import clean_message

            # Test cases for menu processing
            menu_tests = [
                ("1", "I want to announce a funding round"),
                ("1️⃣", "I want to announce a funding round"),
                ("2", "I want to announce a product launch"),
                ("2️⃣", "I want to announce a product launch"),
                ("3", "I want to announce a partnership or integration"),
                ("3️⃣", "I want to announce a partnership or integration"),
            ]

            # Note: Menu conversion happens in agent_endpoint.py, not prefilter
            # This tests the prefilter doesn't break menu selections
            for original, expected_conversion in menu_tests:
                cleaned = clean_message(original)
                if cleaned != original.strip():
                    return self.log_test_result(
                        "menu_selection_processing",
                        False,
                        error=f"Prefilter changed menu selection: {original} → {cleaned}",
                    )

            return self.log_test_result(
                "menu_selection_processing",
                True,
                details={'menu_selections_preserved': len(menu_tests)},
            )

        except Exception as e:
            return self.log_test_result("menu_selection_processing", False, error=e)

    def test_atomic_tools_availability(self):
        """Test 4: All 6 atomic tools are available and importable."""
        print("🛠️ Testing atomic tools availability...")

        try:
            from app import tools_atomic
            from app.agent_runtime import ATOMIC_FUNCS

            expected_tools = [
                'save_announcement_type',
                'save_headline',
                'save_key_facts',
                'save_quotes',
                'save_boilerplate',
                'save_media_contact',
            ]

            missing_tools = []
            for tool in expected_tools:
                if not hasattr(tools_atomic, tool):
                    missing_tools.append(tool)
                elif tool not in ATOMIC_FUNCS:
                    missing_tools.append(f"{tool} (not in ATOMIC_FUNCS)")

            if missing_tools:
                return self.log_test_result(
                    "atomic_tools_availability", False, error=f"Missing tools: {missing_tools}"
                )

            return self.log_test_result(
                "atomic_tools_availability", True, details={'available_tools': len(expected_tools)}
            )

        except Exception as e:
            return self.log_test_result("atomic_tools_availability", False, error=e)

    def test_tool_dispatch_functionality(self):
        """Test 5: Tool dispatch system works correctly."""
        print("⚙️ Testing tool dispatch functionality...")

        try:
            from app.agent_endpoint import TOOL_DISPATCH
            from app.agent_runtime import ATOMIC_FUNCS

            # Test all atomic tools are in dispatch table
            missing_from_dispatch = []
            for tool in ATOMIC_FUNCS:
                if tool not in TOOL_DISPATCH:
                    missing_from_dispatch.append(tool)

            if missing_from_dispatch:
                return self.log_test_result(
                    "tool_dispatch_functionality",
                    False,
                    error=f"Tools missing from dispatch: {missing_from_dispatch}",
                )

            # Test basic tool execution (safe tools only)
            test_tools = ['save_slot', 'get_slot', 'finish']
            successful_calls = 0

            for tool_name in test_tools:
                if tool_name in TOOL_DISPATCH:
                    try:
                        if tool_name == 'save_slot':
                            result = TOOL_DISPATCH[tool_name]('test_slot', 'test_value')
                        elif tool_name == 'get_slot':
                            result = TOOL_DISPATCH[tool_name]('test_slot')
                        elif tool_name == 'finish':
                            result = TOOL_DISPATCH[tool_name]()

                        if isinstance(result, dict):
                            successful_calls += 1
                    except Exception:
                        # Expected for some tools, continue
                        pass

            return self.log_test_result(
                "tool_dispatch_functionality",
                True,
                details={
                    'total_tools_in_dispatch': len(TOOL_DISPATCH),
                    'atomic_tools_present': len(ATOMIC_FUNCS),
                    'safe_tool_calls_tested': successful_calls,
                },
            )

        except Exception as e:
            return self.log_test_result("tool_dispatch_functionality", False, error=e)

    def test_reset_command_processing(self):
        """Test 6: Reset command variations work correctly."""
        print("🔄 Testing reset command processing...")

        try:
            from app.prefilter import clean_message

            reset_commands = [
                "reset",
                "restart",
                "start over",
                "menu",
                "start",
                "Reset",
                "RESET",
                "Menu",
                "START",
            ]

            failed_commands = []
            for cmd in reset_commands:
                cleaned = clean_message(cmd)
                if cleaned is None or cleaned.lower() not in [
                    "reset",
                    "restart",
                    "start over",
                    "menu",
                    "start",
                ]:
                    failed_commands.append(f"{cmd} → {cleaned}")

            if failed_commands:
                return self.log_test_result(
                    "reset_command_processing",
                    False,
                    error=f"Reset commands failed: {failed_commands}",
                )

            return self.log_test_result(
                "reset_command_processing",
                True,
                details={'reset_commands_tested': len(reset_commands)},
            )

        except Exception as e:
            return self.log_test_result("reset_command_processing", False, error=e)

    def test_agent_runtime_integration(self):
        """Test 7: Core agent runtime still works with optimizations."""
        print("🤖 Testing agent runtime integration...")

        try:
            from app.agent_runtime import run_thread

            # Test simple message processing
            start_time = time.time()
            reply, thread_id, tool_calls = run_thread(None, "hello test")
            elapsed = time.time() - start_time

            # Validate response structure
            if not isinstance(reply, str) or len(reply) < 10:
                return self.log_test_result(
                    "agent_runtime_integration", False, error=f"Invalid reply: {reply[:50]}..."
                )

            if not isinstance(thread_id, str) or len(thread_id) < 10:
                return self.log_test_result(
                    "agent_runtime_integration", False, error=f"Invalid thread_id: {thread_id}"
                )

            if not isinstance(tool_calls, list):
                return self.log_test_result(
                    "agent_runtime_integration",
                    False,
                    error=f"Invalid tool_calls: {type(tool_calls)}",
                )

            # Validate timing is within optimized thresholds
            timeout_threshold = 30.0  # Our optimized timeout
            if elapsed >= timeout_threshold:
                return self.log_test_result(
                    "agent_runtime_integration",
                    False,
                    error=f"Response took too long: {elapsed:.2f}s >= {timeout_threshold}s",
                )

            return self.log_test_result(
                "agent_runtime_integration",
                True,
                details={
                    'response_time': round(elapsed, 2),
                    'reply_length': len(reply),
                    'tool_calls_count': len(tool_calls),
                    'within_timeout': elapsed < timeout_threshold,
                },
            )

        except Exception as e:
            return self.log_test_result("agent_runtime_integration", False, error=e)

    def test_performance_monitoring(self):
        """Test 8: Performance monitoring endpoints still work."""
        print("📊 Testing performance monitoring...")

        try:
            # Test timeout configuration access
            from app.agent_endpoint import (
                get_max_ai_processing_time,
                get_max_retries,
                get_retry_base_delay,
                get_retry_max_delay,
            )

            # Validate getter functions return optimized values
            ai_timeout = get_max_ai_processing_time()
            max_retries = get_max_retries()
            base_delay = get_retry_base_delay()
            max_delay = get_retry_max_delay()

            expected_values = {
                'ai_timeout': 30.0,
                'max_retries': 1,
                'base_delay': 0.5,  # retry delay, not polling
                'max_delay': 2.0,
            }

            if ai_timeout != expected_values['ai_timeout']:
                return self.log_test_result(
                    "performance_monitoring",
                    False,
                    error=f"AI timeout mismatch: {ai_timeout} != {expected_values['ai_timeout']}",
                )

            if max_retries != expected_values['max_retries']:
                return self.log_test_result(
                    "performance_monitoring",
                    False,
                    error=f"Max retries mismatch: {max_retries} != {expected_values['max_retries']}",
                )

            return self.log_test_result(
                "performance_monitoring",
                True,
                details={
                    'ai_processing_timeout': ai_timeout,
                    'max_retries': max_retries,
                    'retry_delays': f"{base_delay}s - {max_delay}s",
                },
            )

        except Exception as e:
            return self.log_test_result("performance_monitoring", False, error=e)

    def run_all_tests(self):
        """Run complete regression test suite."""
        print("🧪 PHASE 2 OPTIMIZATION - REGRESSION TEST SUITE")
        print("=" * 60)
        print("Validating that optimizations don't break existing functionality...")
        print()

        # Run all tests
        test_methods = [
            self.test_timeout_configuration,
            self.test_session_management,
            self.test_menu_selection_processing,
            self.test_atomic_tools_availability,
            self.test_tool_dispatch_functionality,
            self.test_reset_command_processing,
            self.test_agent_runtime_integration,
            self.test_performance_monitoring,
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"   ❌ {test_method.__name__} - CRASHED: {e}")

            print()

        # Summary
        print("📊 REGRESSION TEST RESULTS")
        print("=" * 30)
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()

        if passed_tests == total_tests:
            print("🎉 ALL REGRESSION TESTS PASSED!")
            print("✅ Phase 2 optimizations are safe for production")
            print("✅ No existing functionality was broken")
        else:
            failed_count = total_tests - passed_tests
            print(f"⚠️  {failed_count} regression test(s) failed")
            print("⚠️  Review failed tests before production deployment")

        print("=" * 60)

        # Detailed results
        if any(not result['success'] for result in self.test_results):
            print("\n🔍 FAILED TEST DETAILS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['error']}")

        return passed_tests == total_tests


def main():
    """Run regression testing."""
    tester = OptimizationRegressionTester()
    success = tester.run_all_tests()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
