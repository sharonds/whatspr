"""Security validation and request protection utilities.

Provides comprehensive security features including Twilio webhook validation,
rate limiting, input sanitization, and privacy-preserving logging.
"""

import os
import re
import time
import hashlib
from collections import defaultdict
from typing import Optional
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from pydantic import BaseModel, validator
from .config import settings
import structlog

log = structlog.get_logger("security")

# Initialize Twilio validator only if auth token is available
twilio_validator = None
if settings.twilio_auth_token:
    twilio_validator = RequestValidator(settings.twilio_auth_token)


class SecurityConfig:
    """Security configuration management with environment validation.

    Provides methods for validating API keys and environment variables
    required for secure operation of the application.
    """

    @classmethod
    def get_openai_key(cls) -> str:
        """Retrieve and validate OpenAI API key from environment.

        Returns:
            str: Valid OpenAI API key.

        Raises:
            ValueError: If API key is missing or has invalid format.
        """
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        if not key.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")

        return key

    @classmethod
    def validate_environment(cls) -> bool:
        """Validate all required environment variables.

        Checks that all critical environment variables are present and
        have valid formats required for application security.

        Returns:
            bool: True if all environment variables are valid, False otherwise.
        """
        try:
            cls.get_openai_key()
            return True
        except ValueError as e:
            log.error("environment_validation_failed", error=str(e))
            return False


class SecureMessageRequest(BaseModel):
    """Pydantic model for validating incoming WhatsApp message requests.

    Provides validation for phone number format and message content
    with security-focused sanitization and length limits.
    """

    From: str
    Body: str

    @validator("From")
    def validate_phone_number(cls, v):
        """Validate phone number format and structure.

        Args:
            v: Phone number string to validate.

        Returns:
            str: Validated phone number in international format.

        Raises:
            ValueError: If phone number format is invalid.
        """
        if not v:
            raise ValueError("Phone number is required")

        # Must start with + for international format
        if not v.startswith("+"):
            raise ValueError("Phone number must be in international format")

        # Remove + and check if remaining chars are digits
        phone_digits = v[1:]
        if not phone_digits.isdigit():
            raise ValueError("Phone number contains invalid characters")

        # Basic length validation (7-15 digits)
        if len(phone_digits) < 7 or len(phone_digits) > 15:
            raise ValueError("Phone number length invalid")

        return v

    @validator("Body")
    def validate_message_body(cls, v):
        """Validate and sanitize message body content.

        Args:
            v: Message body content to validate.

        Returns:
            str: Sanitized message body with control characters removed.

        Raises:
            ValueError: If message is too long or contains invalid content.
        """
        if v is None:
            return ""

        # Prevent extremely long messages (potential DoS)
        if len(v) > 4000:  # WhatsApp limit is ~4096 chars
            raise ValueError("Message too long")

        # Basic sanitization - remove control characters except newlines/tabs
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", v)

        return sanitized.strip()


def log_security_event(event_type: str, details: dict, phone: Optional[str] = None):
    """Log security events with privacy-preserving phone number hashing.

    Args:
        event_type: Type of security event (e.g., 'rate_limit_exceeded').
        details: Additional event details to log.
        phone: Optional phone number to include (will be hashed for privacy).
    """
    # Hash phone number for privacy
    phone_hash = None
    if phone:
        phone_hash = hashlib.sha256(phone.encode()).hexdigest()[-8:]

    log.info("security_event", event=event_type, phone_hash=phone_hash, **details)


# Simple in-memory rate limiting (for production, use Redis)
_rate_limit_storage = defaultdict(list)


def validate_request_rate(phone: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Validate request rate limits for phone numbers.

    Implements sliding window rate limiting to prevent abuse. Uses in-memory
    storage for simplicity (production should use Redis).

    Args:
        phone: Phone number to check rate limits for.
        max_requests: Maximum allowed requests in the time window.
        window_seconds: Time window in seconds for rate limiting.

    Returns:
        bool: True if request is allowed, False if rate limit exceeded.
    """
    now = time.time()
    phone_requests = _rate_limit_storage[phone]

    # Clean old requests
    phone_requests[:] = [req_time for req_time in phone_requests if now - req_time < window_seconds]

    # Check if under limit
    if len(phone_requests) >= max_requests:
        log_security_event("rate_limit_exceeded", {"requests": len(phone_requests)}, phone)
        return False

    # Add current request
    phone_requests.append(now)
    return True


def get_security_headers() -> dict:
    """Generate security headers for HTTP responses.

    Returns:
        dict: Security headers to prevent common web vulnerabilities.
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }


async def ensure_twilio(request: Request):
    """Validate Twilio webhook signature for request authenticity.

    Verifies that the incoming request is actually from Twilio by
    validating the X-Twilio-Signature header against the request payload.
    Skips validation if no Twilio auth token is configured (test environments).

    Args:
        request: FastAPI request object containing Twilio webhook data.

    Raises:
        HTTPException: 403 Forbidden if signature validation fails.
    """
    # Skip validation if no Twilio auth token configured (test environments)
    if not twilio_validator:
        log.debug("twilio_validation_skipped", reason="no_auth_token")
        return
    
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    if not twilio_validator.validate(url, dict(form), signature):
        log.warning("bad_signature", url=url)
        raise HTTPException(status_code=403, detail="Invalid signature")
