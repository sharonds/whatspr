# New Developer Onboarding Guide

Welcome to the WhatsPR project! This guide will get you set up and ready to contribute to our AI-powered WhatsApp press release chatbot.

## 🚀 Quick Start Checklist

- [ ] **Prerequisites installed** (Python 3.9+, Git, VS Code/PyCharm recommended)
- [ ] **Repository cloned** and virtual environment created
- [ ] **Pre-commit hooks installed** for automated code quality
- [ ] **Environment variables configured** (API keys set up)
- [ ] **All quality checks passing** (lint script runs successfully)
- [ ] **First test commit made** to verify setup
- [ ] **Documentation reviewed** (development guidelines and coding standards)

## 📋 Prerequisites

### Required Software
```bash
# Verify Python version (3.9+)
python3 --version

# Verify Git installation
git --version

# Verify pip installation
python3 -m pip --version
```

### Recommended IDE Setup
- **VS Code**: Python extension + Black formatter extension
- **PyCharm**: Configure Google docstring templates
- **Any editor**: Ensure it supports pre-commit hooks

## 🛠️ Environment Setup

### 1. Clone and Create Virtual Environment

```bash
# Clone the repository
git clone <repository-url>
cd whatspr-staging

# Create and activate virtual environment
python3 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install Pre-commit Hooks

**CRITICAL**: This step ensures all code meets quality standards:

```bash
# Install pre-commit hooks (runs quality checks on every commit)
pre-commit install

# Verify installation
pre-commit --version
```

### 3. Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your API keys
# NEVER commit this file to git!
nano .env  # or use your preferred editor
```

**Required environment variables:**
```
OPENAI_API_KEY=sk-your-openai-key-here
TWILIO_AUTH_TOKEN=your-twilio-auth-token-here
```

### 4. Initialize Database

```bash
# Create database tables
python3 -c "from app.models import init_db; init_db()"
```

### 5. Verify Setup

Run the comprehensive quality check to ensure everything is working:

```bash
# This runs pydocstyle, black, ruff, and pytest
./scripts/lint.sh

# Expected output: "✅ All checks passed!"
```

If any checks fail, see the [Troubleshooting](#troubleshooting) section below.

## 📚 Understanding the Codebase

### Project Structure Overview

```
whatspr-staging/
├── app/                    # Main application code
│   ├── agent.py           # Core AI agent logic
│   ├── agent_endpoint.py  # WhatsApp webhook handler
│   ├── agent_runtime.py   # OpenAI Assistant integration
│   ├── tools_atomic.py    # Six specialized data collection tools
│   ├── security.py        # Security validation and rate limiting
│   ├── models.py          # Database models
│   └── main.py           # FastAPI application setup
├── tests/                 # Comprehensive test suite
│   ├── e2e/              # End-to-end conversation tests
│   ├── test_*.py         # Unit tests for each component
├── docs/                  # Project documentation
├── scripts/lint.sh       # Automated quality check script
└── .pre-commit-config.yaml # Pre-commit hooks configuration
```

### Key Concepts

1. **Atomic Tools System**: Six specialized functions for structured data collection
2. **Goal-Oriented Agent**: Conversational AI that adapts to user input
3. **Security First**: Input validation, rate limiting, and privacy protection
4. **Quality Enforcement**: Automated documentation and code quality standards

## 🎯 Your First Contribution

### Step 1: Test Your Setup

```bash
# Create a feature branch
git checkout -b feat/test-setup

# Make a small change (add a comment to any file)
echo "# Test comment" >> app/main.py

# Try to commit (this will trigger pre-commit hooks)
git add .
git commit -m "test: verify development setup"
```

If the commit succeeds, your setup is working correctly!

### Step 2: Clean Up

```bash
# Remove the test comment
git reset --hard HEAD~1
git checkout main
git branch -D feat/test-setup
```

### Step 3: Explore the Code

Start by reading these key files in order:
1. `app/main.py` - Application entry point
2. `app/agent_endpoint.py` - WhatsApp message handling
3. `app/tools_atomic.py` - Data collection tools
4. `tests/e2e/test_conversation_flow.py` - End-to-end testing examples

## 📖 Development Standards

### Code Quality Requirements

Our project has **zero tolerance** for quality violations:

1. **Google-style docstrings**: Every function, class, and module must have complete documentation
2. **Black formatting**: Code must be formatted with 100-character line length
3. **Ruff linting**: No linting errors allowed
4. **Test coverage**: All new features require tests
5. **Pre-commit hooks**: Must pass before any commit
6. **CI/CD**: GitHub Actions must pass on all PRs

### Documentation Standards

Every function needs a docstring like this:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """Brief description of what the function does.
    
    More detailed description if needed. Explain the purpose,
    behavior, and any important implementation details.
    
    Args:
        param1: Description of first parameter.
        param2: Description of second parameter with default.
        
    Returns:
        bool: Description of return value.
        
    Raises:
        ValueError: When param1 is empty.
        
    Example:
        Basic usage:
        
        >>> result = example_function("test", 42)
        >>> print(result)
        True
    """
    # Implementation here
    pass
```

See [docs/DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md) for complete standards.

### Git Workflow

```bash
# Always create feature branches
git checkout -b feat/descriptive-name

# Make atomic commits with conventional commit format
git commit -m "feat: add new functionality"
git commit -m "fix: resolve bug in component"
git commit -m "docs: update function documentation"

# Pre-commit hooks run automatically on each commit
# Push and create PR when ready
git push -u origin feat/descriptive-name
```

## 🛠️ Development Workflow

### Daily Development

```bash
# Start your day
git checkout main && git pull

# Create feature branch
git checkout -b feat/your-feature

# Make changes, run quality checks frequently
./scripts/lint.sh

# Commit often (pre-commit hooks run automatically)
git add . && git commit -m "feat: implement feature part 1"

# Before pushing, ensure everything passes
./scripts/lint.sh
git push -u origin feat/your-feature
```

### Before Submitting PRs

```bash
# Final quality check
./scripts/lint.sh

# Ensure all tests pass
pytest tests/ -v

# Check that no secrets were accidentally added
grep -r "sk-" . --exclude-dir=.git --exclude-dir=env

# Verify pre-commit hooks are working
pre-commit run --all-files
```

## 🔧 Troubleshooting

### Common Setup Issues

#### Pre-commit Hooks Not Running
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Test manually
pre-commit run --all-files
```

#### Quality Checks Failing

**Docstring Issues:**
```bash
# Check specific docstring errors
pydocstyle app/ --convention=google

# Common fix: Add missing docstrings to functions
```

**Formatting Issues:**
```bash
# Auto-fix formatting
black app/ --line-length=100

# Check formatting
black --check --diff app/
```

**Linting Issues:**
```bash
# Auto-fix many issues
ruff check app/ --fix

# Manual fixes required for remaining issues
ruff check app/
```

#### Environment Variable Issues

```bash
# Verify .env file exists and has correct variables
cat .env

# Verify .env is in .gitignore
grep -E "\.env$" .gitignore
```

#### Database Issues

```bash
# Recreate database
rm -f whatspr.db
python3 -c "from app.models import init_db; init_db()"
```

### Testing Issues

```bash
# Run specific test categories
pytest tests/test_safety.py -v          # Security tests
pytest tests/test_tools_atomic.py -v    # Atomic tools tests
pytest tests/e2e/ -v -s                 # End-to-end tests (verbose)

# Run with full output for debugging
pytest tests/ -v -s --tb=long
```

### IDE Configuration

**VS Code Settings (`.vscode/settings.json`):**
```json
{
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=100"],
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "autoDocstring.docstringFormat": "google"
}
```

**PyCharm Configuration:**
1. Settings → Tools → External Tools → Add Black formatter
2. Settings → Editor → Code Style → Python → Docstrings → Google format
3. Enable ruff as external linter

## 🔍 Learning Resources

### Understanding the Architecture

1. **Read the docs**: Start with [docs/DEVELOPMENT.md](DEVELOPMENT.md)
2. **Explore tests**: `tests/e2e/` shows complete conversation flows
3. **Study atomic tools**: `app/tools_atomic.py` is the core data collection system
4. **Review security**: `app/security.py` shows our security model

### Key Files to Understand

- `app/agent_runtime.py` - OpenAI Assistant integration
- `app/agent_endpoint.py` - WhatsApp webhook handling  
- `prompts/assistant_v2.txt` - AI agent conversation prompt
- `knowledge/press_release_requirements.txt` - External knowledge base

### Testing Approach

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete conversation flows
- **Security tests**: Verify no secrets are exposed

## 🚀 Ready to Contribute?

Once you've completed this onboarding:

1. **Join the development workflow** outlined in [docs/DEVELOPMENT.md](DEVELOPMENT.md)
2. **Pick up your first issue** from the project backlog
3. **Ask questions** - the team is here to help!
4. **Follow code review guidelines** for smooth PR processes

## 📞 Getting Help

- **Documentation questions**: Check [docs/DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md)
- **Development questions**: Review [docs/DEVELOPMENT.md](DEVELOPMENT.md)  
- **Security questions**: See [SECURITY.md](../SECURITY.md)
- **General questions**: Create an issue or reach out to the team

Welcome to the team! 🎉

---

**Next Steps**: After completing this onboarding, review [docs/DEVELOPMENT.md](DEVELOPMENT.md) for detailed development workflows and architecture information.