"""Tests for rate limiting functionality.

Verifies that rate limiting is properly applied to API calls
to prevent overwhelming external services and improve test reliability.
"""

import time
import threading
from tests.utils.rate_limiter import (
    RateLimiter,
    get_rate_limiter,
    rate_limit,
    rate_limit_test,
    RateLimitedTestCase,
    ServiceRateLimiters,
)


class TestRateLimiter:
    """Test the RateLimiter class functionality."""

    def test_basic_rate_limiting(self):
        """Test that rate limiter properly controls call rate."""
        limiter = RateLimiter(calls_per_second=2, burst_size=2)

        start_time = time.time()

        # Should allow 2 calls immediately (burst)
        limiter.acquire()
        limiter.acquire()

        # Third call should be delayed
        limiter.acquire()

        elapsed = time.time() - start_time

        # Should take at least 0.5 seconds (1/2 calls per second)
        assert elapsed >= 0.4  # Allow small timing variance

    def test_burst_capacity(self):
        """Test that burst capacity works correctly."""
        limiter = RateLimiter(calls_per_second=1, burst_size=3)

        # Should allow 3 calls immediately
        start_time = time.time()
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        elapsed = time.time() - start_time

        # These should be instant (within burst)
        assert elapsed < 0.1

        # Fourth call should be delayed
        start_time = time.time()
        limiter.acquire()
        elapsed = time.time() - start_time

        # Should wait approximately 1 second
        assert elapsed >= 0.9  # Allow small timing variance

    def test_token_refill(self):
        """Test that tokens are refilled over time."""
        limiter = RateLimiter(calls_per_second=2, burst_size=2)

        # Use all tokens
        limiter.acquire()
        limiter.acquire()

        # Wait for refill
        time.sleep(1)

        # Should have 2 tokens available again
        start_time = time.time()
        limiter.acquire()
        limiter.acquire()
        elapsed = time.time() - start_time

        # Should be instant after refill
        assert elapsed < 0.1


class TestRateLimiterThreadSafety:
    """Test thread safety of rate limiter."""

    def test_concurrent_access(self):
        """Test that rate limiter is thread-safe."""
        limiter = RateLimiter(calls_per_second=5, burst_size=5)
        results = []

        def make_call(thread_id):
            """Simulate a rate-limited API call."""
            start = time.time()
            limiter.acquire()
            end = time.time()
            results.append((thread_id, start, end))

        # Start 10 threads simultaneously
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_call, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have all 10 results
        assert len(results) == 10

        # Sort by completion time
        results.sort(key=lambda x: x[2])

        # First 5 should complete quickly (burst)
        for i in range(5):
            assert results[i][2] - results[0][2] < 0.2

        # Next 5 should be rate limited
        for i in range(5, 10):
            # Each should wait approximately 0.2 seconds (1/5 per second)
            expected_delay = (i - 4) * 0.2
            actual_delay = results[i][2] - results[0][2]
            assert abs(actual_delay - expected_delay) < 0.3  # Allow variance


class TestRateLimitDecorator:
    """Test the rate_limit decorator."""

    def test_decorator_basic(self):
        """Test that decorator applies rate limiting."""
        call_times = []

        @rate_limit(service="test", calls_per_second=2, burst_size=1)
        def api_call():
            call_times.append(time.time())
            return "success"

        # First call should be instant
        start = time.time()
        result = api_call()
        assert result == "success"
        assert time.time() - start < 0.1

        # Second call should be delayed
        start = time.time()
        result = api_call()
        assert result == "success"
        assert time.time() - start >= 0.4  # ~0.5 seconds

    def test_decorator_preserves_function(self):
        """Test that decorator preserves function attributes."""

        @rate_limit(service="test")
        def my_function(x, y):
            """Test function."""
            return x + y

        # Function name and doc should be preserved
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "Test function."

        # Function should still work
        assert my_function(2, 3) == 5


class TestRateLimitTestDecorator:
    """Test the rate_limit_test decorator."""

    def test_test_decorator(self):
        """Test that test decorator works correctly."""
        execution_times = []

        @rate_limit_test(calls_per_second=3, burst_size=1)
        def test_function():
            execution_times.append(time.time())

        # Run multiple times
        for _ in range(3):
            test_function()

        # Check timing
        assert len(execution_times) == 3

        # First should be instant
        # Second should wait ~0.33 seconds
        # Third should wait ~0.33 seconds
        if len(execution_times) >= 2:
            assert execution_times[1] - execution_times[0] >= 0.25
        if len(execution_times) >= 3:
            assert execution_times[2] - execution_times[1] >= 0.25


class TestRateLimitedTestCase:
    """Test the RateLimitedTestCase base class."""

    def test_base_class_functionality(self):
        """Test that base class provides rate limiting."""

        class MyTestCase(RateLimitedTestCase):
            CALLS_PER_SECOND = 2
            BURST_SIZE = 1

            def __init__(self):
                self.call_times = []

            def api_function(self):
                self.call_times.append(time.time())
                return "result"

        test_case = MyTestCase()
        test_case.setup_method(lambda: None)

        # Make multiple API calls
        start = time.time()
        result1 = test_case.make_api_call(test_case.api_function)
        elapsed1 = time.time() - start

        start = time.time()
        result2 = test_case.make_api_call(test_case.api_function)
        elapsed2 = time.time() - start

        # First should be instant
        assert elapsed1 < 0.1
        assert result1 == "result"

        # Second should be delayed
        assert elapsed2 >= 0.4  # ~0.5 seconds
        assert result2 == "result"


class TestServiceRateLimiters:
    """Test pre-configured service rate limiters."""

    def test_openai_config(self):
        """Test OpenAI rate limiter configuration."""
        config = ServiceRateLimiters.OPENAI
        assert config["service"] == "openai"
        assert config["calls_per_second"] == 0.5
        assert config["burst_size"] == 3

    def test_twilio_config(self):
        """Test Twilio rate limiter configuration."""
        config = ServiceRateLimiters.TWILIO
        assert config["service"] == "twilio"
        assert config["calls_per_second"] == 2.0
        assert config["burst_size"] == 10

    def test_default_config(self):
        """Test default rate limiter configuration."""
        config = ServiceRateLimiters.DEFAULT
        assert config["service"] == "default"
        assert config["calls_per_second"] == 1.0
        assert config["burst_size"] == 5


class TestGlobalRateLimiters:
    """Test global rate limiter management."""

    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns singleton instances."""
        limiter1 = get_rate_limiter("test_service", 1.0, 5)
        limiter2 = get_rate_limiter("test_service", 2.0, 10)  # Different params

        # Should return the same instance (params ignored after first call)
        assert limiter1 is limiter2

    def test_different_services_different_limiters(self):
        """Test that different services get different limiters."""
        limiter1 = get_rate_limiter("service1", 1.0, 5)
        limiter2 = get_rate_limiter("service2", 1.0, 5)

        # Should be different instances
        assert limiter1 is not limiter2
