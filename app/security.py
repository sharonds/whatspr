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
twilio_validator = RequestValidator(settings.twilio_auth_token)


class SecurityConfig:
    """Security configuration with validation."""

    @classmethod
    def get_openai_key(cls) -> str:
        """Get OpenAI API key with validation."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if not key.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        
        return key

    @classmethod
    def validate_environment(cls) -> bool:
        """Validate all required environment variables are present and valid."""
        try:
            cls.get_openai_key()
            return True
        except ValueError as e:
            log.error("environment_validation_failed", error=str(e))
            return False


class SecureMessageRequest(BaseModel):
    """Validated request model for incoming messages."""
    
    From: str
    Body: str
    
    @validator('From')
    def validate_phone_number(cls, v):
        """Validate phone number format."""
        if not v:
            raise ValueError("Phone number is required")
        
        # Must start with + for international format
        if not v.startswith('+'):
            raise ValueError("Phone number must be in international format")
        
        # Remove + and check if remaining chars are digits
        phone_digits = v[1:]
        if not phone_digits.isdigit():
            raise ValueError("Phone number contains invalid characters")
        
        # Basic length validation (7-15 digits)
        if len(phone_digits) < 7 or len(phone_digits) > 15:
            raise ValueError("Phone number length invalid")
        
        return v
    
    @validator('Body')
    def validate_message_body(cls, v):
        """Validate message body content."""
        if v is None:
            return ""
        
        # Prevent extremely long messages (potential DoS)
        if len(v) > 4000:  # WhatsApp limit is ~4096 chars
            raise ValueError("Message too long")
        
        # Basic sanitization - remove control characters except newlines/tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        
        return sanitized.strip()


def log_security_event(event_type: str, details: dict, phone: Optional[str] = None):
    """Log security-related events for monitoring."""
    # Hash phone number for privacy
    phone_hash = None
    if phone:
        phone_hash = hashlib.sha256(phone.encode()).hexdigest()[-8:]
    
    log.info(
        "security_event",
        event=event_type,
        phone_hash=phone_hash,
        **details
    )


# Simple in-memory rate limiting (for production, use Redis)
_rate_limit_storage = defaultdict(list)

def validate_request_rate(phone: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Basic rate limiting validation."""
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
    """Get security headers for responses."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY", 
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }


async def ensure_twilio(request: Request):
    """Validate Twilio webhook signature."""
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form = await request.form()
    if not twilio_validator.validate(url, dict(form), signature):
        log.warning("bad_signature", url=url)
        raise HTTPException(status_code=403, detail="Invalid signature")
