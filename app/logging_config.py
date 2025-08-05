"""Structured logging configuration with PII scrubbing.

Configures structlog for JSON logging with timestamp and privacy protection
for sensitive information like phone numbers and email addresses.
"""

import logging
import structlog
import sys


def scrub_pii(logger, _, event):
    """Remove personally identifiable information from log events.

    Args:
        logger: Logger instance (unused).
        _: Log method name (unused).
        event: Log event dictionary to scrub.

    Returns:
        dict: Event dictionary with PII fields masked.
    """
    for k in ("phone", "email"):
        if k in event:
            event[k] = "***"
    return event


def configure_logging(level=logging.INFO):
    """Configure structured logging with JSON output and PII protection.

    Args:
        level: Logging level (default: INFO).
    """
    logging.basicConfig(stream=sys.stdout, format="%(message)s", level=level)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(level),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            scrub_pii,
            structlog.processors.JSONRenderer(),
        ],
    )
