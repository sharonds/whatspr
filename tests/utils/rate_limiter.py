"""Rate limiting utilities for API tests.

This module provides rate limiting decorators and utilities to prevent
overwhelming external APIs during test execution, improving test reliability
and reducing API quota consumption.
"""

import time
import threading
from functools import wraps
from typing import Dict, Callable, Any


class RateLimiter:
    """Thread-safe rate limiter for API calls.

    Implements a simple token bucket algorithm to control the rate of API calls.
    """

    def __init__(self, calls_per_second: float = 1.0, burst_size: int = 5):
        """Initialize the rate limiter.

        Args:
            calls_per_second: Maximum sustained rate of calls per second
            burst_size: Maximum number of calls that can be made in a burst
        """
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket, blocking if necessary.

        Args:
            tokens: Number of tokens to acquire
        """
        with self.lock:
            # Refill tokens based on time elapsed
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.calls_per_second

            if tokens_to_add > 0:
                self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
                self.last_refill = now

            # Wait if not enough tokens
            while self.tokens < tokens:
                time.sleep(0.1)
                now = time.time()
                elapsed = now - self.last_refill
                tokens_to_add = elapsed * self.calls_per_second

                if tokens_to_add > 0:
                    self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
                    self.last_refill = now

            # Consume tokens
            self.tokens -= tokens


# Global rate limiters for different API services
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(
    service: str = "default", calls_per_second: float = 1.0, burst_size: int = 5
) -> RateLimiter:
    """Get or create a rate limiter for a specific service.

    Args:
        service: Name of the service (e.g., "openai", "twilio")
        calls_per_second: Maximum sustained rate of calls per second
        burst_size: Maximum number of calls that can be made in a burst

    Returns:
        RateLimiter instance for the service
    """
    if service not in _rate_limiters:
        _rate_limiters[service] = RateLimiter(calls_per_second, burst_size)
    return _rate_limiters[service]


def rate_limit(
    service: str = "default", calls_per_second: float = 1.0, burst_size: int = 5, tokens: int = 1
) -> Callable:
    """Decorator to rate limit function calls.

    Args:
        service: Name of the service to rate limit
        calls_per_second: Maximum sustained rate of calls per second
        burst_size: Maximum number of calls that can be made in a burst
        tokens: Number of tokens this call consumes

    Returns:
        Decorated function with rate limiting applied
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            limiter = get_rate_limiter(service, calls_per_second, burst_size)
            limiter.acquire(tokens)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit_test(calls_per_second: float = 0.5, burst_size: int = 2) -> Callable:
    """Decorator specifically for test functions that make API calls.

    Args:
        calls_per_second: Maximum sustained rate of calls per second
        burst_size: Maximum number of calls that can be made in a burst

    Returns:
        Decorated test function with rate limiting applied
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Use test-specific rate limiter
            limiter = get_rate_limiter(f"test_{func.__name__}", calls_per_second, burst_size)
            limiter.acquire()
            return func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitedTestCase:
    """Base class for test cases that need rate limiting.

    Provides automatic rate limiting for all test methods that make API calls.
    """

    # Default rate limits for test cases
    CALLS_PER_SECOND = 0.5  # 1 call every 2 seconds
    BURST_SIZE = 2  # Allow 2 calls in quick succession

    def setup_method(self, method):
        """Set up rate limiting for the test method."""
        self.rate_limiter = get_rate_limiter(
            f"test_case_{self.__class__.__name__}_{method.__name__}",
            self.CALLS_PER_SECOND,
            self.BURST_SIZE,
        )
        # Call parent setup if exists
        if hasattr(super(), 'setup_method'):
            super().setup_method(method)

    def make_api_call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Make a rate-limited API call.

        Args:
            func: The function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call
        """
        self.rate_limiter.acquire()
        return func(*args, **kwargs)


# Pre-configured rate limiters for common services
class ServiceRateLimiters:
    """Pre-configured rate limiters for common services."""

    # OpenAI: Be conservative to avoid hitting rate limits
    OPENAI = {
        "service": "openai",
        "calls_per_second": 0.5,  # 1 call every 2 seconds
        "burst_size": 3,
    }

    # Twilio: More lenient as it's usually more tolerant
    TWILIO = {"service": "twilio", "calls_per_second": 2.0, "burst_size": 10}

    # Default for unknown services
    DEFAULT = {"service": "default", "calls_per_second": 1.0, "burst_size": 5}
