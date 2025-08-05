# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in WhatsPR, please report it responsibly:

- **Email**: [Create an appropriate security contact email]
- **Response Time**: We aim to respond within 24 hours
- **Disclosure**: Please allow us time to fix the issue before public disclosure

## Security Best Practices

### Environment Variables

**NEVER commit these to git:**
- `OPENAI_API_KEY`
- `TWILIO_AUTH_TOKEN`
- Any files ending in `.key`, `.pem`, or containing `secret`

**CRITICAL**: The `OPENAI_API_KEY` must be available before module import to prevent authentication failures. The application uses lazy initialization to handle environment variable loading, but proper setup is essential for reliability.

### Development Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your credentials** (never commit .env file)

3. **Verify .env is in .gitignore:**
   ```bash
   grep -E "\.env$" .gitignore
   ```

### API Key Security

- **OpenAI Keys**: Start with `sk-` and are ~64 characters
- **Twilio Tokens**: 32-character hexadecimal strings
- **Rotation**: Rotate keys immediately if exposed
- **Monitoring**: Set up billing alerts to detect unauthorized usage

### Production Deployment

1. **Use environment variables** (not .env files):
   ```bash
   export OPENAI_API_KEY="your-key-here"
   export TWILIO_AUTH_TOKEN="your-token-here"
   ```

2. **Use secrets management:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets
   - GitHub Secrets (for CI/CD)

3. **Enable security features:**
   - Rate limiting (implemented in `app/security.py`)
   - Request validation
   - Security headers
   - Twilio signature verification

## Security Features

### Input Validation (`app/security.py`)

**Phone Number Validation:**
```python
@validator('From')
def validate_phone_number(cls, v):
    # Must be international format (+1234567890)
    # 7-15 digits after country code
    # Only numeric characters allowed
```

**Message Sanitization:**
```python
@validator('Body') 
def validate_message_body(cls, v):
    # Maximum 4000 characters (WhatsApp limit)
    # Control character removal
    # Basic XSS prevention
```

### Rate Limiting

**Implementation:**
```python
def validate_request_rate(phone: str, max_requests: int = 10, window_seconds: int = 60):
    # In-memory storage for development
    # Redis recommended for production
    # Automatic cleanup of expired requests
```

**Configuration:**
- Default: 10 requests per minute per phone number
- Configurable limits per endpoint
- Security event logging for violations
- Graceful degradation when limits exceeded

### Security Headers

Applied to all responses via `get_security_headers()`:

```http
X-Content-Type-Options: nosniff           # Prevent MIME sniffing
X-Frame-Options: DENY                     # Prevent clickjacking  
X-XSS-Protection: 1; mode=block          # XSS protection
Referrer-Policy: strict-origin-when-cross-origin  # Referrer control
```

### Webhook Security

**Twilio Signature Verification:**
```python
async def ensure_twilio(request: Request):
    signature = request.headers.get("X-Twilio-Signature", "")
    # Validates request authenticity using HMAC-SHA1
    # Prevents unauthorized webhook calls
```

**Request Authentication:**
- HMAC signature validation
- URL and payload integrity checks
- Automatic rejection of invalid requests

### Privacy Protection

**Phone Number Hashing:**
```python
def log_security_event(event_type: str, details: dict, phone: Optional[str] = None):
    phone_hash = hashlib.sha256(phone.encode()).hexdigest()[-8:]
    # Only last 8 characters of hash stored in logs
```

**Data Minimization:**
- No full phone numbers in logs
- Sensitive data truncated in debug output
- User data encrypted at rest (when applicable)

### Environment Security

**Configuration Validation:**
```python
class SecurityConfig:
    @classmethod
    def validate_environment(cls) -> bool:
        # Validates API key format
        # Checks required environment variables
        # Logs validation failures
```

**Key Format Validation:**
- OpenAI keys must start with `sk-`
- Twilio tokens must be 32-character hex
- Automatic validation on startup

## Monitoring

### Security Events Logged
- Rate limit violations
- Invalid signatures
- Environment validation failures
- Suspicious request patterns

### Log Format
```json
{
  "event": "security_event",
  "phone_hash": "abc12345",
  "details": {...}
}
```

## Security Testing

### Automated Testing

**Security Test Suite (`tests/test_safety.py`):**
```bash
pytest tests/test_safety.py -v
```

**Tests Include:**
- No production secrets in repository
- Environment variable validation
- Input sanitization verification
- Rate limiting functionality
- Security header presence

### Manual Security Checks

**Pre-deployment Security Checklist:**
```bash
# 1. Check for exposed secrets
grep -r "sk-" . --exclude-dir=.git --exclude-dir=env || echo "✅ No keys found"

# 2. Verify environment validation
python -c "from app.security import SecurityConfig; print('✅ Valid' if SecurityConfig.validate_environment() else '❌ Invalid')"

# 3. Test rate limiting
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=+1234567890&Body=test" \
  # Repeat 11+ times to trigger rate limit

# 4. Verify security headers
curl -I http://localhost:8000/agent
```

### Penetration Testing

**Common Attack Vectors to Test:**
- SQL injection via message body
- XSS attempts in user input
- Rate limit bypass attempts
- Invalid phone number formats
- Oversized message payloads
- Webhook signature bypassing

### Security Metrics

**Key Performance Indicators:**
- Rate limit violations per hour
- Invalid request attempts
- Failed authentication attempts
- API key validation failures
- Security event frequency

## Incident Response

### Security Incident Classification

**Severity Levels:**
- **Critical**: API keys exposed, data breach, system compromise
- **High**: Failed authentication, rate limit abuse, suspicious patterns
- **Medium**: Input validation failures, minor security violations  
- **Low**: Normal security events, informational logs

### API Key Exposure Response

**IMMEDIATE (0-30 minutes):**
1. **Rotate compromised keys**:
   - OpenAI: https://platform.openai.com/api-keys
   - Twilio: Console > Account > API Keys
2. **Set billing alerts** on both services
3. **Monitor usage dashboards** for unauthorized activity

**URGENT (30 minutes - 2 hours):**
1. **Remove from git history**:
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch .env' \
     --prune-empty --tag-name-filter cat -- --all
   ```
2. **Force push** to remove from remote (coordinate with team)
3. **Notify team members** of the incident

**FOLLOW-UP (2-24 hours):**
1. **Review logs** for unauthorized usage patterns
2. **Update security procedures** to prevent recurrence
3. **Consider external security audit** for critical incidents
4. **Document lessons learned**

### Rate Limit Abuse Response

**Detection:**
```python
# Automatic logging when rate limits exceeded
log_security_event("rate_limit_exceeded", {"requests": count}, phone)
```

**Response Actions:**
1. **Identify source**: Check phone number patterns
2. **Increase monitoring**: Add additional alerting
3. **Adjust limits**: Temporary reduction if needed
4. **Block if necessary**: Implement IP-based blocking for severe abuse

### Unauthorized Access Attempts

**Webhook Signature Failures:**
```python
# Logged automatically in ensure_twilio()
log.warning("bad_signature", url=url)
```

**Response Protocol:**
1. **Verify legitimacy**: Confirm Twilio configuration
2. **Check patterns**: Look for systematic attempts
3. **Update security**: Rotate webhook secrets if compromised
4. **Alert team**: Notify of potential security issues

### Contact Information

- **Security Team**: [Add appropriate contact]
- **Emergency**: [Add emergency contact for critical issues]

## Compliance

This project implements security measures appropriate for:
- WhatsApp Business API integration
- OpenAI API usage
- Personal data handling (phone numbers are hashed in logs)

## Updates

This security policy is reviewed and updated regularly. Last updated: [Current Date]