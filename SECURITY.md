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

### Input Validation
- Phone number format validation
- Message length limits (4000 characters)
- Control character sanitization

### Rate Limiting
- Default: 10 requests per minute per phone number
- Configurable via `validate_request_rate()`
- Logs rate limit violations

### Security Headers
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Webhook Verification
- Twilio signature validation
- Request authenticity verification

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

## Incident Response

### If API Keys Are Exposed

1. **IMMEDIATE (0-30 minutes):**
   - Rotate all exposed keys
   - Set billing alerts
   - Monitor usage dashboards

2. **URGENT (30 minutes - 2 hours):**
   - Remove from git history
   - Force push to remove from remote
   - Notify team members

3. **FOLLOW-UP (2-24 hours):**
   - Review logs for unauthorized usage
   - Update security procedures
   - Consider security audit

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