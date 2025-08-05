#!/usr/bin/env python3
"""
WhatsApp Failure Diagnostic Monitor
Real-time analysis to identify the 50% failure bottleneck
"""

import requests
import time
import os
from datetime import datetime


class WhatsAppDiagnostics:
    def __init__(self):
        self.base_url = "http://localhost:8004"
        self.results = []

    def test_openai_api_health(self):
        """Test OpenAI API directly to isolate API issues"""
        print("🧪 Testing OpenAI API health...")

        try:
            import openai

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ No OPENAI_API_KEY found in environment")
                return False, 0

            client = openai.OpenAI(api_key=api_key)

            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello, test message"}],
                max_tokens=50,
                timeout=10.0,
            )
            elapsed = time.time() - start_time
            print(f"✅ OpenAI API responding in {elapsed:.2f}s")
            print(f"   Response: {response.choices[0].message.content[:100]}...")
            return True, elapsed
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            print(f"❌ OpenAI API failed after {elapsed:.2f}s: {e}")
            return False, elapsed

    def test_whatsapp_endpoint(self, message_body="We raised 250K from Elon Musk"):
        """Test the exact WhatsApp endpoint that's failing"""

        test_data = {
            "From": "whatsapp:+31621366440",
            "Body": message_body,
            "MessageSid": f"TEST_{int(time.time())}",
        }

        print(f"📱 Testing: '{message_body[:50]}...'")
        start_time = time.time()

        try:
            response = requests.post(
                f"{self.base_url}/agent",
                data=test_data,
                timeout=25,  # Longer than our 8s timeout to catch everything
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            elapsed = time.time() - start_time

            # Analyze response type
            if response.status_code != 200:
                result_type = f"http_error_{response.status_code}"
                success = False
            elif "trouble processing" in response.text:
                result_type = "generic_error_response"  # This is the 50% failure case!
                success = False
            elif "processing your request" in response.text:
                result_type = "timeout_fallback_response"  # Our timeout protection
                success = False
            elif "Message>" in response.text and len(response.text) > 200:
                result_type = "successful_ai_response"
                success = True
            elif "Message>" in response.text:
                result_type = "short_ai_response"
                success = True
            else:
                result_type = "unexpected_format"
                success = False

            # Extract actual message content for analysis
            response_preview = (
                response.text[:200] + "..." if len(response.text) > 200 else response.text
            )

            status_icon = "✅" if success else "❌"
            print(
                f"{status_icon} {elapsed:.2f}s | 📊 {response.status_code} | 📝 {len(response.text)} chars | {result_type}"
            )
            print(f"   Preview: {response_preview}")

            return {
                'success': success,
                'elapsed': elapsed,
                'result_type': result_type,
                'status_code': response.status_code,
                'response_length': len(response.text),
                'response_preview': response_preview,
                'message': message_body,
            }

        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            print(f"❌ TIMEOUT after {elapsed:.2f}s")
            return {
                'success': False,
                'elapsed': elapsed,
                'result_type': 'timeout',
                'message': message_body,
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ ERROR after {elapsed:.2f}s: {e}")
            return {
                'success': False,
                'elapsed': elapsed,
                'result_type': 'error',
                'message': message_body,
                'error': str(e),
            }

    def test_server_health(self):
        """Test basic server connectivity"""
        print("🏥 Testing server health endpoints...")

        # Test root endpoint
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            print(f"✅ Root endpoint: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")

        # Test agent endpoint with minimal data
        try:
            response = requests.post(
                f"{self.base_url}/agent", data={"From": "test", "Body": "reset"}, timeout=10
            )
            print(f"✅ Agent endpoint basic test: {response.status_code}")
        except Exception as e:
            print(f"❌ Agent endpoint failed: {e}")

    def check_system_resources(self):
        """Check if system resources could be the bottleneck"""
        print("💻 Checking system resources...")

        try:
            import psutil

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"📊 CPU Usage: {cpu_percent}%")

            # Memory usage
            memory = psutil.virtual_memory()
            print(
                f"📊 Memory Usage: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)"
            )

            # Find our processes
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'uvicorn' in proc.info['name'] or 'python' in proc.info['name']:
                        print(
                            f"🔍 Process {proc.info['name']} (PID {proc.info['pid']}): CPU {proc.info['cpu_percent']:.1f}%, Memory {proc.info['memory_percent']:.1f}%"
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except ImportError:
            print("📊 psutil not available, checking basic stats...")
            import subprocess

            try:
                # Basic CPU check on macOS
                result = subprocess.run(
                    ['top', '-l', '1'], capture_output=True, text=True, timeout=5
                )
                cpu_line = [line for line in result.stdout.split('\n') if 'CPU usage' in line]
                if cpu_line:
                    print(f"📊 {cpu_line[0].strip()}")
            except Exception as e:
                print(f"📊 Could not get system stats: {e}")

    def run_comprehensive_test(self):
        """Run comprehensive failure analysis"""
        print("🔍 Starting Comprehensive WhatsApp Failure Analysis...")
        print("=" * 70)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # Test 0: System health
        print("\n0️⃣ System Health Check:")
        self.check_system_resources()

        # Test 1: Server connectivity
        print("\n1️⃣ Testing Server Health:")
        self.test_server_health()

        # Test 2: OpenAI API Health
        print("\n2️⃣ Testing OpenAI API Health:")
        openai_success, openai_time = self.test_openai_api_health()

        # Test 3: Production failure scenario (the exact one failing)
        print("\n3️⃣ Testing Production Failure Scenario:")
        prod_result = self.test_whatsapp_endpoint("We raised 250K from Elon Musk")
        self.results.append(prod_result)

        # Test 4: Simple message
        print("\n4️⃣ Testing Simple Message:")
        simple_result = self.test_whatsapp_endpoint("1")
        self.results.append(simple_result)

        # Test 5: Complex message
        print("\n5️⃣ Testing Complex Message:")
        complex_result = self.test_whatsapp_endpoint(
            "We are TechCorp and we just raised $15M Series A from Venture Partners. Our CEO Jane Smith said this will accelerate our mission."
        )
        self.results.append(complex_result)

        # Test 6: Multiple rapid tests to reproduce 50% failure rate
        print("\n6️⃣ Testing Rapid Fire (10 messages to reproduce 50% failure):")
        rapid_results = []
        for i in range(10):
            print(f"   Test {i+1}/10:")
            result = self.test_whatsapp_endpoint(f"Test message {i+1}: We raised funding")
            rapid_results.append(result)
            self.results.append(result)
            time.sleep(0.5)  # Brief pause to avoid overwhelming

        # Analyze results
        self.analyze_results(openai_success, openai_time)

    def analyze_results(self, openai_success, openai_time):
        """Analyze test results to identify bottlenecks"""
        print("\n" + "=" * 70)
        print("📊 DIAGNOSTIC ANALYSIS RESULTS")
        print("=" * 70)

        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failure_rate = (total_tests - successful_tests) / total_tests * 100

        print(f"🎯 Success Rate: {successful_tests}/{total_tests} ({100-failure_rate:.1f}%)")
        print(f"🚨 Failure Rate: {failure_rate:.1f}%")

        if failure_rate >= 50:
            print("🚨 HIGH FAILURE RATE DETECTED - CRITICAL ISSUE CONFIRMED")
        elif failure_rate >= 20:
            print("⚠️  MODERATE FAILURE RATE - NEEDS ATTENTION")
        else:
            print("✅ LOW FAILURE RATE - WITHIN ACCEPTABLE RANGE")

        # Analyze failure types
        failure_types = {}
        response_times = []

        for result in self.results:
            if not result['success']:
                failure_type = result['result_type']
                failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
            response_times.append(result['elapsed'])

        print("\n📈 Response Time Stats:")
        print(f"   Average: {sum(response_times)/len(response_times):.2f}s")
        print(f"   Min: {min(response_times):.2f}s")
        print(f"   Max: {max(response_times):.2f}s")

        if failure_types:
            print("\n🔍 Failure Type Breakdown:")
            for failure_type, count in failure_types.items():
                percentage = (count / total_tests) * 100
                print(f"   {failure_type}: {count} occurrences ({percentage:.1f}%)")

        # Identify likely bottleneck
        print("\n🎯 BOTTLENECK ANALYSIS:")

        if not openai_success:
            print(
                "🚨 CRITICAL: OpenAI API is NOT responding - This is likely the primary bottleneck"
            )
        elif openai_time > 5:
            print(f"⚠️  OpenAI API is slow ({openai_time:.2f}s) - May contribute to timeouts")
        else:
            print(f"✅ OpenAI API is healthy ({openai_time:.2f}s)")

        if 'generic_error_response' in failure_types:
            count = failure_types['generic_error_response']
            print(f"🚨 CRITICAL: {count} generic error responses - Internal processing failures")
            print("   This suggests OpenAI API calls are failing within the application")

        if 'timeout_fallback_response' in failure_types:
            count = failure_types['timeout_fallback_response']
            print(f"⚠️  {count} timeout fallback responses - AI processing taking >8s")

        if 'timeout' in failure_types:
            print("⚠️  Request timeouts detected - Server overwhelmed or hung")

        avg_time = sum(response_times) / len(response_times)
        if avg_time > 15:
            print("⚠️  SLOW RESPONSES - Exceeding Twilio timeout limits")

        # Specific recommendations
        print("\n💡 RECOMMENDED NEXT STEPS:")

        if not openai_success:
            print("   1. 🚨 URGENT: Check OpenAI API key and account status")
            print("   2. 🚨 URGENT: Check OpenAI API rate limits and billing")
            print("   3. Check network connectivity to OpenAI")

        if 'generic_error_response' in failure_types and failure_rate > 30:
            print("   1. Check server logs: tail -50 server_diagnostic.log")
            print("   2. Check for OpenAI API errors in application logs")
            print("   3. Implement better error logging in agent_runtime.py")
            print("   4. Consider circuit breaker pattern for OpenAI calls")

        if failure_rate > 50:
            print("   🚨 IMMEDIATE ACTION REQUIRED:")
            print("   - Implement emergency fallback responses")
            print("   - Add comprehensive error logging")
            print("   - Consider OpenAI API status page check")

        print("\n📋 Log Analysis Commands:")
        print("   tail -50 server_diagnostic.log | grep -E '(error|exception|failed)'")
        print("   tail -100 server_diagnostic.log | grep -E '(ai_timeout|ai_error)'")
        print("   curl -s https://status.openai.com/api/v2/status.json | python3 -m json.tool")


if __name__ == "__main__":
    print("🚀 WhatsApp Failure Diagnostic Monitor")
    print("=" * 50)

    diagnostics = WhatsAppDiagnostics()
    diagnostics.run_comprehensive_test()

    print(f"\n🏁 Diagnostic completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
