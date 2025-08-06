"""Centralized timeout configuration management.

This module provides centralized management for all timeout values used across
the application, ensuring consistency and easy configuration updates.
"""

import os
import logging
from typing import Dict, Any, Optional
from threading import Lock

log = logging.getLogger(__name__)


class TimeoutConfig:
    """Central configuration class for all timeout values."""

    def __init__(
        self,
        openai_request_timeout: float = 10.0,
        ai_processing_timeout: float = 25.0,
        polling_max_attempts: int = 20,
        polling_base_delay: float = 0.5,
        polling_max_delay: float = 4.0,
        retry_max_attempts: int = 2,
        retry_base_delay: float = 0.5,
        retry_max_delay: float = 2.0,
        profile: Optional[str] = None,
    ):
        """Initialize timeout configuration with validation.

        Args:
            openai_request_timeout: Timeout for OpenAI API requests
            ai_processing_timeout: Total timeout for AI processing
            polling_max_attempts: Maximum polling attempts
            polling_base_delay: Base delay between polling attempts
            polling_max_delay: Maximum delay between polling attempts
            retry_max_attempts: Maximum retry attempts
            retry_base_delay: Base delay between retries
            retry_max_delay: Maximum delay between retries
            profile: Environment profile (development, staging, production)
        """
        # Validate timeout values
        if any(val <= 0 for val in [openai_request_timeout, ai_processing_timeout]):
            raise ValueError("All timeout values must be positive")

        if ai_processing_timeout <= openai_request_timeout:
            raise ValueError("AI processing timeout must be greater than OpenAI request timeout")

        if polling_max_attempts < 5:
            raise ValueError("Polling attempts must be at least 5")

        # Validate production values
        if profile == 'production':
            if openai_request_timeout < 1.0:
                raise ValueError("Timeout too short for production")

        # Validate maximum values
        if openai_request_timeout > 120 or ai_processing_timeout > 300:
            raise ValueError("Timeout too long")

        self.openai_request_timeout = openai_request_timeout
        self.ai_processing_timeout = ai_processing_timeout
        self.polling_max_attempts = polling_max_attempts
        self.polling_base_delay = polling_base_delay
        self.polling_max_delay = polling_max_delay
        self.retry_max_attempts = retry_max_attempts
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return (
            self.ai_processing_timeout > self.openai_request_timeout
            and all(
                val > 0
                for val in [
                    self.openai_request_timeout,
                    self.ai_processing_timeout,
                    self.polling_base_delay,
                    self.retry_base_delay,
                ]
            )
            and self.polling_max_attempts >= 5
        )

    @classmethod
    def from_env(cls) -> 'TimeoutConfig':
        """Create configuration from environment variables."""

        def get_float(key: str, default: float) -> float:
            try:
                return float(os.environ.get(key, default))
            except (ValueError, TypeError):
                return default

        def get_int(key: str, default: int) -> int:
            try:
                return int(os.environ.get(key, default))
            except (ValueError, TypeError):
                return default

        return cls(
            openai_request_timeout=get_float('OPENAI_REQUEST_TIMEOUT', 10.0),
            ai_processing_timeout=get_float('AI_PROCESSING_TIMEOUT', 25.0),
            polling_max_attempts=get_int('POLLING_MAX_ATTEMPTS', 20),
            polling_base_delay=get_float('POLLING_BASE_DELAY', 0.5),
            polling_max_delay=get_float('POLLING_MAX_DELAY', 4.0),
            retry_max_attempts=get_int('RETRY_MAX_ATTEMPTS', 2),
            retry_base_delay=get_float('RETRY_BASE_DELAY', 0.5),
            retry_max_delay=get_float('RETRY_MAX_DELAY', 2.0),
        )

    @classmethod
    def for_profile(cls, profile: str) -> 'TimeoutConfig':
        """Create configuration for specific environment profile."""
        if profile == 'development':
            return cls(
                openai_request_timeout=5.0,
                ai_processing_timeout=15.0,
                retry_max_attempts=1,
            )
        elif profile == 'staging':
            return cls(
                openai_request_timeout=8.0,
                ai_processing_timeout=20.0,
                retry_max_attempts=2,
            )
        elif profile == 'production':
            return cls(
                openai_request_timeout=15.0,
                ai_processing_timeout=30.0,
                retry_max_attempts=3,
            )
        else:
            raise ValueError(f"Unknown profile: {profile}")

    def compare(self, other: 'TimeoutConfig') -> Dict[str, tuple]:
        """Compare with another configuration."""
        differences = {}
        for attr in [
            'openai_request_timeout',
            'ai_processing_timeout',
            'polling_max_attempts',
            'retry_max_attempts',
        ]:
            if getattr(self, attr) != getattr(other, attr):
                differences[attr] = (getattr(self, attr), getattr(other, attr))
        return differences

    def __eq__(self, other) -> bool:
        """Check equality with another configuration."""
        if not isinstance(other, TimeoutConfig):
            return False
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in [
                'openai_request_timeout',
                'ai_processing_timeout',
                'polling_max_attempts',
                'retry_max_attempts',
            ]
        )


class TimeoutManager:
    """Singleton timeout manager for runtime configuration management."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Create new instance with validation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize timeout configuration."""
        if not self._initialized:
            try:
                # Check if we have an environment profile setting
                import os
                profile = os.environ.get("ENVIRONMENT")
                if profile and profile in ['development', 'staging', 'production']:
                    self.config = TimeoutConfig.for_profile(profile)
                else:
                    self.config = TimeoutConfig.from_env()
            except Exception as e:
                log.warning(f"Failed to initialize TimeoutConfig: {e}, using defaults")
                self.config = TimeoutConfig()

            self._config_updates_count = 0
            self._last_updated = None
            self._timeout_stats = {}
            self._initialized = True

    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return getattr(self, '_initialized', False)

    def update_config(self, new_config: TimeoutConfig):
        """Update configuration at runtime."""
        with self._lock:
            self.config = new_config
            self._config_updates_count += 1
            self._last_updated = __import__('datetime').datetime.now()

        log.info(
            "timeout_config_updated",
            extra={'new_config': new_config.__dict__, 'update_count': self._config_updates_count},
        )

    def temporary_config(self, **overrides):
        """Context manager for temporary configuration overrides."""
        return _TemporaryConfigContext(self, overrides)

    def reload_from_env(self):
        """Hot-reload configuration from environment."""
        new_config = TimeoutConfig.from_env()
        self.update_config(new_config)

    def get_metrics(self) -> Dict[str, Any]:
        """Get timeout manager metrics."""
        return {
            'current_config': self.config.__dict__,
            'config_updates_count': self._config_updates_count,
            'last_updated': self._last_updated.isoformat() if self._last_updated else None,
        }

    def record_timeout_event(
        self, event_type: str, actual_duration: float, configured_timeout: float
    ):
        """Record timeout event for monitoring."""
        if event_type not in self._timeout_stats:
            self._timeout_stats[event_type] = {
                'durations': [],
                'timeout_usage_ratios': [],
                'total_events': 0,
            }

        stats = self._timeout_stats[event_type]
        stats['durations'].append(actual_duration)
        stats['timeout_usage_ratios'].append(actual_duration / configured_timeout)
        stats['total_events'] += 1

        # Keep only last 100 events
        if len(stats['durations']) > 100:
            stats['durations'] = stats['durations'][-100:]
            stats['timeout_usage_ratios'] = stats['timeout_usage_ratios'][-100:]

    def get_timeout_stats(self) -> Dict[str, Any]:
        """Get timeout statistics."""
        result = {}
        for event_type, stats in self._timeout_stats.items():
            if stats['durations']:
                result[event_type] = {
                    'average_duration': sum(stats['durations']) / len(stats['durations']),
                    'timeout_usage_ratio': sum(stats['timeout_usage_ratios'])
                    / len(stats['timeout_usage_ratios']),
                    'total_events': stats['total_events'],
                }
        return result

    def detect_legacy_timeouts(self) -> Dict[str, Any]:
        """Detect legacy hardcoded timeouts in codebase."""
        # This would scan for hardcoded timeout values in production
        legacy_values = {}
        if legacy_values:
            log.warning("legacy_timeout_detected", extra=legacy_values)
        return legacy_values


class _TemporaryConfigContext:
    """Context manager for temporary timeout configuration."""

    def __init__(self, manager: TimeoutManager, overrides: Dict[str, Any]):
        self.manager = manager
        self.overrides = overrides
        self.original_config = None

    def __enter__(self):
        self.original_config = self.manager.config

        # Create new config with overrides
        config_dict = self.original_config.__dict__.copy()
        config_dict.update(self.overrides)

        new_config = TimeoutConfig(
            **{
                k: v
                for k, v in config_dict.items()
                if k
                in [
                    'openai_request_timeout',
                    'ai_processing_timeout',
                    'polling_max_attempts',
                    'polling_base_delay',
                    'polling_max_delay',
                    'retry_max_attempts',
                    'retry_base_delay',
                    'retry_max_delay',
                ]
            }
        )

        self.manager.config = new_config
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.config = self.original_config


# Global timeout manager instance
timeout_manager = TimeoutManager()
