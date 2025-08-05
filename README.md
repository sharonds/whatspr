# WhatsPR - AI-Powered Press Release Agent

FastAPI chatbot for WhatsApp using Twilio that creates press releases through conversational AI.

**🆕 Latest Updates**: OpenAI API connection reliability fix (resolved 50% failure rate) + Complete code quality enforcement system with Google-style docstrings, automated formatting, comprehensive linting, and CI/CD pipeline integration.

## 🚀 Features

### Core Functionality
* **AI-Powered Conversations**: Natural language press release creation using OpenAI GPT
* **Atomic Tools System**: 6 specialized tools for structured data collection
* **Goal-Oriented Agent**: Conversational flow that adapts to user input
* **Knowledge Base Integration**: External requirements file for intelligent responses

### Production-Ready Security
* **Input Validation**: Phone number and message sanitization
* **Rate Limiting**: 10 requests/minute per phone number  
* **Security Headers**: XSS protection, frame options, content type validation
* **Request Sanitization**: Control character filtering and length limits
* **Privacy Protection**: Hashed phone numbers in logs

### Infrastructure
* **Twilio Integration**: HMAC signature verification for webhook security
* **SQLite Persistence**: Database storage with atomic operations
* **Structured Logging**: JSON logging with `structlog` for monitoring
* **Request Middleware**: Latency tracking and error handling
* **Comprehensive Testing**: Unit tests, E2E tests, and security validation

### Code Quality Enforcement
* **Automated Documentation**: Complete Google-style docstring coverage (0 pydocstyle errors)
* **Code Formatting**: Black formatter with 100-character line length
* **Comprehensive Linting**: Ruff for style, quality, and best practices
* **Pre-commit Hooks**: Automatic quality checks on every commit
* **CI/CD Pipeline**: GitHub Actions enforces standards on all PRs
* **Zero Tolerance**: No code merged without passing all quality checks

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- OpenAI API key
- Twilio account with auth token
- Git (for pre-commit hooks)

### Quick Start

```bash
# Clone and setup environment
cd whatspr-staging
python -m venv env && source env/bin/activate
pip install -r requirements.txt

# Install pre-commit hooks for automated code quality
pre-commit install

# Configure environment (NEVER commit .env file!)
cp .env.example .env
# Edit .env and add your API keys:
#   OPENAI_API_KEY=sk-your-key-here
#   TWILIO_AUTH_TOKEN=your-32-char-token

# Verify setup with complete quality checks
./scripts/lint.sh                          # Runs all quality checks
pytest tests/ -v                           # Should pass 28+ tests

# Start development server
uvicorn app.main:app --reload --port 8000

# For WhatsApp integration
ngrok http 8000                            # Paste URL into Twilio sandbox webhook
```

### 🔒 Security Setup

**CRITICAL**: Never commit API keys to git!

```bash
# Verify .env is in .gitignore
grep -E "\.env$" .gitignore

# Check for exposed secrets (should return nothing)
grep -r "sk-" . --exclude-dir=.git --exclude-dir=env || echo "✅ No keys found"
```

### ⚠️ Environment Variables - Critical Requirements

**IMPORTANT**: The `OPENAI_API_KEY` must be available before module import to prevent authentication failures.

```bash
# Required environment variables:
OPENAI_API_KEY=sk-your-openai-key-here    # CRITICAL: Must be set before app starts
TWILIO_AUTH_TOKEN=your-32-char-token       # Required for webhook verification

# Verify API key is accessible:
python -c "import os; print('✅ API key found' if os.environ.get('OPENAI_API_KEY') else '❌ API key missing')"
```

The application uses lazy initialization to handle environment variable loading, but proper setup prevents reliability issues.

## 🧪 Testing

### Test Suites Available

```bash
# Run all tests
pytest tests/ -v

# Specific test categories
pytest tests/test_tools_atomic.py -v      # Atomic tools functionality
pytest tests/test_safety.py -v            # Security validations
pytest tests/e2e/ -v                      # End-to-end conversation flows
pytest tests/test_reliability.py -v       # OpenAI API reliability testing
```

### 🔧 Diagnostic Tools

For troubleshooting connection and reliability issues:

```bash
# Quick diagnostic script (immediate insights)
python test_diagnose.py

# Comprehensive reliability testing
pytest tests/test_reliability.py -v --tb=short

# Check OpenAI API connection
python -c "from app.agent_runtime import get_client; print('✅ API connection OK' if get_client().models.list() else '❌ Connection failed')"
```

### E2E Testing
The E2E test suite simulates complete WhatsApp conversations:

- **Happy Path Flow**: Tests complete press release creation flow
- **Edge Cases**: Corrections, knowledge base queries, difficult inputs
- **Tool Validation**: Verifies atomic tools are called correctly
- **Rate Limiting**: Tests security features

## 🏗️ Architecture

### Atomic Tools System
Six specialized tools for structured data collection:

- `save_announcement_type` - Type of announcement (funding, product, etc.)  
- `save_headline` - Press release headline
- `save_key_facts` - Core facts (who, what, when, amount)
- `save_quotes` - Spokesperson and investor quotes
- `save_boilerplate` - Company description
- `save_media_contact` - Contact information (name • email • phone)

### Agent Runtime
- **Goal-Oriented Conversations**: Natural dialogue flow using `prompts/assistant_v2.txt`
- **Knowledge Integration**: External requirements file for intelligent responses
- **Context Management**: Persistent conversation state across messages
- **Error Recovery**: Graceful handling of corrections and invalid inputs

## 📊 Monitoring & Logging

### Security Events
All security-related events are logged with structured data:

```json
{
  "event": "security_event",
  "phone_hash": "abc12345",
  "event_type": "rate_limit_exceeded",
  "details": {"requests": 15}
}
```

### Performance Metrics
- Request latency tracking
- Tool execution monitoring  
- Error rate monitoring
- API usage tracking

## 🚀 Deployment

### Production Checklist

- [ ] **API Keys Rotated**: Never use development keys in production
- [ ] **Environment Variables**: Use secure secrets management (OPENAI_API_KEY must be available at startup)
- [ ] **Monitoring**: Set up alerts for security events and errors
- [ ] **Rate Limits**: Configure appropriate limits for production load
- [ ] **Backup**: Database backup strategy in place
- [ ] **Reliability Testing**: Run `pytest tests/test_reliability.py` before deployment

### 🚨 Troubleshooting Common Issues

**50% Failure Rate / Authentication Errors:**
```bash
# 1. Check if API key is set correctly
echo $OPENAI_API_KEY | head -c 10

# 2. Remove stale assistant cache (forces recreation)
rm -f .assistant_id .assistant_id.staging

# 3. Run diagnostic script
python test_diagnose.py

# 4. Test API connection directly
python -c "from app.agent_runtime import get_client; print(get_client().models.list().data[0].id)"
```

**Module Import Issues:**
- Ensure `OPENAI_API_KEY` is in environment before importing `app.agent_runtime`
- Use lazy initialization pattern for API clients
- Check `.env` file is being loaded correctly

### Cloud Deployment

```bash
# Example for Cloud Run
gcloud run deploy whatspr \
  --source . \
  --platform managed \
  --region us-central1 \
  --min-instances 1 \
  --set-env-vars OPENAI_API_KEY=${OPENAI_API_KEY},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
```

## 📚 Documentation

### Core Documentation
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)**: Complete development workflow and architecture guide
- **[docs/ONBOARDING.md](docs/ONBOARDING.md)**: New developer onboarding and setup guide
- **[docs/DOCUMENTATION_GUIDELINES.md](docs/DOCUMENTATION_GUIDELINES.md)**: Google-style docstring standards and enforcement

### Project Documentation  
- **[SECURITY.md](SECURITY.md)**: Security policies and incident response
- **[FINAL_ACCEPTANCE_TEST.md](FINAL_ACCEPTANCE_TEST.md)**: Complete testing procedures
- **[CLAUDE.md](CLAUDE.md)**: AI agent development guidelines

## 🤝 Contributing

### Development Workflow

```bash
# Create feature branch
git checkout -b feat/your-feature-name

# Make changes with automatic quality enforcement
# (pre-commit hooks run automatically on commit)

# Manual quality check (recommended before committing)
./scripts/lint.sh                          # Comprehensive quality check

# Commit with conventional commits (triggers pre-commit hooks)
git add .
git commit -m "feat: add new feature description"
git push -u origin feat/your-feature-name
```

### Code Quality Standards
- **Google-style docstrings**: Complete documentation coverage enforced via pydocstyle
- **Automated formatting**: Black formatter with 100-character line length  
- **Linting**: Ruff for code quality and style enforcement
- **Pre-commit hooks**: Automatic quality checks before each commit
- **CI/CD pipeline**: GitHub Actions enforces quality standards on all PRs
- **Zero tolerance**: No PRs merged without passing all quality checks
- **Test coverage**: Required for new features
- **Security review**: Required for authentication/validation changes
- **No secrets**: Enforced by pre-commit hooks and CI/CD

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.