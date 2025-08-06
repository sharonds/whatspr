# CLAUDE.md - WhatsPR MVP Context

*Last Updated: August 6, 2025 | MVP Status: Production-Ready Core System*

## 🎯 MVP Overview

### **Core Value Proposition**
WhatsPR transforms press release creation from a 3-hour professional writing task into a 15-minute conversational WhatsApp experience, making professional-quality press releases accessible to every startup and business.

### **Target Users**
Startups and businesses needing professional press releases without hiring expensive PR agencies or having writing expertise.

### **MVP Success Criteria**
- **User Adoption:** Complete press release creation via WhatsApp
- **Core Functionality:** 6 atomic tools for structured data collection work reliably
- **Technical Stability:** 99%+ uptime with <15 second response times

## ✅ Current MVP Status: **SHIPPED & PRODUCTION-READY**

### **Production-Ready Achievements**
- **Session Management**: Complete TTL-based SessionManager with MVP-scale testing (<20 users)
- **Production Safety**: API failure recovery, emergency rollback, health monitoring
- **Rate Limiting**: Token bucket algorithm protecting API quotas
- **Quality Enforcement**: 100% Google-style docstring coverage, zero linting errors  
- **Reliability Fix**: Solved 50% OpenAI API failure rate with lazy initialization
- **Performance Optimization**: Eliminated 20% timeout fallback rate with Phase 2 optimizations
- **Testing Coverage**: 60+ tests with E2E conversation flows + session lifecycle testing
- **Security**: HMAC verification, input sanitization, phone number hashing

---

## 🏗️ Technical Foundation

### **Technology Stack**
- **Backend:** FastAPI + Python 3.12
- **Database:** SQLite (→ PostgreSQL planned)
- **Messaging:** Twilio (WhatsApp Business API)
- **AI:** OpenAI Assistant API with File Search
- **Deployment:** Docker + Cloud Run ready
- **External Services:** OpenAI, Twilio

### **Key Architecture Decisions**
- **Conversation-First Design:** Natural dialogue vs rigid forms
- **Atomic Operations Pattern:** 6 specialized tools prevent data corruption
- **Knowledge-Augmented AI:** External PR knowledge base via File Search
- **TTL-Based Session Management:** Thread-safe sessions with automatic cleanup (MVP: <20 users)

---

## 🔧 Development Workflow

### **Claude Code MVP Workflow (5-Step) - Updated Aug 6, 2025**
**Focus: Ship working features fast, iterate based on feedback**

1. **`/blueprint`** - MVP TDD planning (essential tests only)
2. **Build** - Core functionality implementation
3. **`/qa-review`** - Critical security & production safety
4. **`/update-docs`** - Essential documentation only
5. **`/review-commits` + `/create-pr`** - Clean commits & production-ready PR

**Strategic Planning:** `/strategic-planning` (every 2-3 features)

**MVP Philosophy:** Essential quality gates only, direct production deployment, 3-4 min overhead for professional development cycle.
2. **Build** - Implement with atomic operations and proper error handling
3. **Quality Check** - `./scripts/lint.sh` (100% Google docstring coverage required)
4. **Test** - `pytest tests/ -v` (60+ tests must pass)
5. **Deploy** - Docker-ready with environment validation

### **MVP Development Principles**
- **Ship working features fast** - Perfect later through iteration
- **Essential quality gates only** - No over-engineering
- **User feedback driven** - Build what creates value
- **Plan before coding** - Use TodoWrite for structured approach

### **Strategic Commands**
```bash
# Essential Development Commands
./scripts/lint.sh              # Complete quality check
pytest tests/e2e/ -v           # WhatsApp integration tests
python test_diagnose.py        # System health validation
```

---

## 📊 Core Business Logic

### **MVP User Flow**
```
WhatsApp Message → AI Processing → Atomic Tool → Database → AI Response → User
```

### **6 Atomic Tools for Structured Data Collection**
- **`save_announcement_type`** - Funding, product launch, acquisition, etc.
- **`save_headline`** - Professional headline generation and refinement  
- **`save_key_facts`** - Who, what, when, where, amount details
- **`save_quotes`** - Spokesperson and stakeholder quotes
- **`save_boilerplate`** - Company description and background
- **`save_media_contact`** - Press contact information

### **Knowledge-Driven Content**
- **External Knowledge Base:** `knowledge/press_release_requirements.txt`
- **File Search Integration:** OpenAI Assistant with PR best practices
- **Industry Standards:** Professional press release formatting and structure

---

## 🧪 MVP Testing Strategy

### **Essential Testing Only**
- **Core User Flows:** Complete WhatsApp press release creation
- **API Reliability:** OpenAI and Twilio integration stability  
- **Security Basics:** HMAC verification, input validation, rate limiting

### **Test Organization**
- **E2E Tests:** `tests/e2e/` - Full WhatsApp conversation flows
- **Session Tests:** `tests/test_session_cleanup.py`, `tests/test_mvp_session_lifecycle.py` - Session management
- **Reliability Tests:** `tests/test_reliability.py`, `tests/test_api_failure_recovery.py` - API stability
- **Rate Limiting:** `tests/test_rate_limiting.py` - Quota protection

### **MVP Testing Philosophy**
- **Test core functionality thoroughly** - Press release creation must work
- **Focus on user-breaking bugs** - Not edge case perfection
- **Rate limit all API tests** - Protect quotas during development

---

## 🔐 Essential Security & Quality

### **Security Minimums**
- **Authentication:** Twilio HMAC signature verification
- **Data Protection:** Phone number hashing, input sanitization
- **Rate Limiting:** 10 requests/minute per phone, API quota protection
- **Environment Security:** Lazy initialization prevents API key exposure

### **Code Quality Standards**
- **Google-style docstrings:** 100% coverage enforced via `pydocstyle`
- **Automated formatting:** Black with 100-character line length
- **Pre-commit hooks:** Quality checks before each commit
- **Essential Commands:**
  - `./scripts/lint.sh` - Complete quality validation
  - `pytest tests/ -v` - All tests must pass
  - `python test_diagnose.py` - System health check

---

## 🚀 Production Deployment

### **Environment Setup**
```bash
# Essential Environment Variables
OPENAI_API_KEY=sk-your-openai-key-here    # CRITICAL: Must be set before app starts
TWILIO_AUTH_TOKEN=your-32-char-token       # Required for webhook verification

# Development
uvicorn app.main:app --reload --port 8000
ngrok http 8000                            # For WhatsApp webhook testing
```

### **Deployment Process**
1. **Environment Check:** Verify API keys are configured  
2. **Quality Gates:** `./scripts/lint.sh` and `pytest tests/ -v` must pass
3. **Deploy:** Docker container ready for Cloud Run
4. **Verify:** WhatsApp webhook responds within 15 seconds

### **Health Check**
```bash
# System diagnostic and API validation
python test_diagnose.py                    # Comprehensive system health
curl -I http://localhost:8000/health       # Health endpoint check

# Session Management Health (MVP Deployment)
curl -s /health/sessions | jq              # Session system status
curl -s /health/sessions/details | jq      # Active sessions, memory usage
curl -X POST /health/sessions/cleanup      # Force expired session cleanup
```

---

## 🔄 External Integrations

### **Critical Services**
- **OpenAI Assistant API:** GPT-4 with File Search, lazy initialization prevents auth failures
- **Twilio WhatsApp:** HMAC verified webhooks, 15-second response limit
- **SQLite Database:** Atomic operations, migration path to PostgreSQL planned
- **Session Management:** TTL-based cleanup, thread-safe operations, emergency rollback capability

### **Integration Health**
- **Rate Limiting:** Token bucket algorithm protects API quotas
- **Error Recovery:** Graceful fallbacks for API timeouts, session preservation during failures
- **Security:** HMAC verification, input sanitization, phone hashing, session isolation
- **Monitoring:** Real-time session metrics, memory tracking, automated cleanup

---

## 🎯 Current MVP Priorities

### **Next Development Focus**
1. **User Feedback Integration** - Deploy and gather real user feedback
2. **Cloud Deployment** - Production Cloud Run deployment with optimized performance
3. **Knowledge Base Expansion** - Add more PR examples and best practices
4. **Advanced Features** - Consider Task 2.2-2.4 optimizations based on user feedback

### **Success Metrics to Track**
- **Completion Rate:** Users finishing full press release creation
- **Response Time:** <15 seconds for all WhatsApp responses
- **Error Rate:** <1% system failures
- **User Value:** Professional quality press releases generated

---

## 🐛 Technical Reference

### **OpenAI API Reliability Fix** *(Critical Issue Resolved)*
Fixed 50% failure rate by implementing lazy initialization pattern in `app/agent_runtime.py`:

```python
def get_client():
    """Get or create OpenAI client with proper API key."""
    global _client
    if _client is None:
        # Load API key with fallback to .env
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("OPENAI_API_KEY", "")
        _client = OpenAI(api_key=api_key)
    return _client
```

**Key Learning:** API clients should never be initialized at module import time.

### **Rate Limiting Implementation** *(Development Infrastructure)*
Token bucket algorithm protects API quotas during testing and development:

- **Service-specific limits:** OpenAI (0.5/sec), Twilio (2.0/sec), Default (1.0/sec)
- **Thread-safe implementation:** `tests/utils/rate_limiter.py`
- **Test base class:** `RateLimitedTestCase` for automatic rate limiting
- **Benefits:** Prevents quota exhaustion, cost control, staging safety

### **Timeout Centralization** *(Infrastructure Component)*
Centralized configuration management via `timeout_manager.config`:

- **Dynamic timeouts:** AI processing (25s), retry attempts (3), delay ranges
- **Environment profiles:** Different configs for dev/staging/prod
- **Backward compatibility:** Existing API maintained through getter functions
- **Integration:** `app/agent_endpoint.py` uses centralized values

### **Session Management System** *(Production-Ready MVP Infrastructure)*
TTL-based session management with comprehensive testing for MVP deployment:

- **Thread-Safe Operations:** Concurrent access by multiple users safely handled
- **Automatic Cleanup:** Background TTL expiration prevents memory leaks (5-min intervals)
- **MVP Scale Testing:** Validated for <20 concurrent users with realistic conversation patterns
- **API Failure Recovery:** Sessions preserved during OpenAI/Twilio timeouts
- **Health Monitoring:** Real-time metrics at `/health/sessions` and `/health/sessions/details`
- **Emergency Rollback:** `scripts/rollback_session_manager.py` for critical issues
- **Documentation:** Complete deployment guide at `docs/MVP_SESSION_DEPLOYMENT.md`

### **Phase 2 Performance Optimization** *(Critical Issue Resolved - Aug 2025)*
Eliminated 20% timeout fallback rate that was causing "Oops, temporary error" responses:

**Task 2.1: Timeout Configuration Fix**
- Per-attempt timeout: 8.3s → 15.0s (+80.7% improvement)
- AI processing timeout: 25s → 30s (better OpenAI compatibility)
- Retry attempts: 2 → 1 (focus on success first time)

**Task 2.5: Polling Optimization**  
- Base polling delay: 0.5s → 0.2s (60% reduction)
- Max polling delay: 4.0s → 2.0s (50% reduction)
- Theoretical sleep time reduced by 52.4%

**Validation Results:**
- Timeout fallback rate: 20% → 0% (target: <5%)
- All regression tests passed (8/8 functionality areas)  
- Average response time: 11.68s (within 30s optimized timeout)
- No existing functionality broken

**Implementation:** `app/timeout_config.py` with optimized defaults, comprehensive test suites validate effectiveness.

### **Phase 2.6: Timeout Configuration Loading Fix** *(Critical Production Issue Resolved - Aug 2025)*
Fixed critical configuration loading bug that prevented Phase 2 optimizations from being applied:

**Root Cause:** `ENVIRONMENT='development'` environment variable caused timeout_manager to load development profile settings (15s timeout) instead of Phase 2 optimized values (30s timeout).

**Critical Fix Applied:**
- Updated development profile in `timeout_config.py:117-124` to use Phase 2 optimizations
- Changed `ai_processing_timeout: 15.0` → `30.0` in development profile
- Added Phase 2.5 polling optimizations to development profile
- Ensured consistency across all environment profiles

**Results Achieved:**
- Success rate: 62.5% → **100%** (diagnostic validation)
- Timeout failures: 37.5% → **0%** (complete elimination)
- Server logs confirm `timeout_threshold_ms: 30000.0` (proper 30s timeout)
- Average response time: 9.71s (well within optimized 30s limit)

**Key Learning:** Environment profile loading takes precedence over default values. All profiles must be updated when changing global optimization parameters.

---

## 📋 Quick Reference

### **Essential Commands**
```bash
# Development
uvicorn app.main:app --reload --port 8000  # Local server
ngrok http 8000                            # WhatsApp webhook tunnel

# Quality & Testing  
./scripts/lint.sh                          # Complete quality check
pytest tests/e2e/ -v                       # WhatsApp integration tests
pytest tests/test_session_cleanup.py -v    # Session management tests
python test_diagnose.py                    # System health diagnostic

# Production Health
curl -I http://localhost:8000/health       # Health endpoint check
curl -s /health/sessions/details | jq      # Session system monitoring
```

### **Important Files**
- **Core Logic:** `app/agent_endpoint.py`, `app/tools_atomic.py`
- **Session Management:** `app/session_manager.py`, `app/session_config/session_config.py`
- **Configuration:** `app/timeout_config.py`, `app/config.py`  
- **Knowledge:** `knowledge/press_release_requirements.txt`
- **Tests:** `tests/e2e/test_whatsapp_reliability.py`, `tests/test_session_cleanup.py`
- **Performance Tests:** `test_optimization_regression.py`, `test_quick_fallback_validation.py`
- **Documentation:** `docs/MVP_SESSION_DEPLOYMENT.md`
- **Emergency Scripts:** `scripts/rollback_session_manager.py`

---

*This document serves as the central MVP context for WhatsPR development. Focus on user value delivery through proven technical infrastructure.*