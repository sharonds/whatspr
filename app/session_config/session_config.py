"""Session configuration management.

Provides configuration classes for session cleanup and TTL management.
"""

import os
from dataclasses import dataclass


@dataclass
class SessionConfig:
    """Configuration for session management and cleanup.

    Args:
        ttl_seconds: Time-to-live for sessions in seconds.
        cleanup_interval: How often to run cleanup in seconds.
        allow_test_values: Allow short values for testing purposes.

    Raises:
        ValueError: If configuration values are invalid.
    """

    ttl_seconds: int = 1800  # 30 minutes default
    cleanup_interval: int = 300  # 5 minutes default
    allow_test_values: bool = False  # Allow short values for testing

    def __post_init__(self):
        """Validate configuration after initialization."""
        min_ttl = 1 if self.allow_test_values else 60
        min_cleanup = 1 if self.allow_test_values else 30

        if self.ttl_seconds < min_ttl:
            raise ValueError(f"TTL must be at least {min_ttl} seconds")

        if self.cleanup_interval < min_cleanup:
            raise ValueError(f"Cleanup interval must be at least {min_cleanup} seconds")

        if self.cleanup_interval >= self.ttl_seconds:
            raise ValueError("Cleanup interval should be less than TTL")

    def is_valid(self) -> bool:
        """Check if configuration is valid.

        Returns:
            bool: True if configuration is valid.
        """
        try:
            self.__post_init__()
            return True
        except ValueError:
            return False

    @classmethod
    def from_env(cls) -> 'SessionConfig':
        """Create configuration from environment variables.

        Environment variables:
            SESSION_TTL_SECONDS: Session time-to-live in seconds
            SESSION_CLEANUP_INTERVAL: Cleanup interval in seconds

        Returns:
            SessionConfig: Configuration loaded from environment.
        """
        ttl_seconds = int(os.getenv('SESSION_TTL_SECONDS', '1800'))
        cleanup_interval = int(os.getenv('SESSION_CLEANUP_INTERVAL', '300'))

        return cls(ttl_seconds=ttl_seconds, cleanup_interval=cleanup_interval)
