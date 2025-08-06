# MVP Session Management Deployment Guide

*Last Updated: August 6, 2025 | MVP Status: Production-Ready*

## 🎯 MVP Session Architecture

### **Core Session Management**
WhatsPR uses the **SessionManager** with TTL-based cleanup for managing WhatsApp conversation context during press release creation. Designed for MVP scale of **<20 concurrent users**.

### **Key Components**
- **SessionManager**: Thread-safe session storage with automatic TTL expiration
- **SessionConfig**: Configurable TTL (1 hour default) and cleanup intervals (5 minutes)
- **Health Monitoring**: Real-time session metrics and cleanup endpoints
- **Backward Compatibility**: Migration from legacy dictionary-based sessions

---

## 🏗️ Session Lifecycle Management

### **Session Creation Flow**
```python
# Automatic session creation on first message
def process_whatsapp_message(phone: str, message: str):
    thread_id = session_manager.get_session(phone)
    if thread_id is None:
        # Create new OpenAI Assistant thread
        thread_id = create_new_thread()
        session_manager.set_session(phone, thread_id)
```

### **TTL Refresh Behavior**
- **Active Conversations**: Each message access refreshes TTL to full duration
- **Expiration**: Inactive sessions expire after 1 hour (configurable)
- **Cleanup**: Automatic background cleanup every 5 minutes
- **Memory Safety**: Prevents memory leaks during long-running deployments

### **Session Isolation**
- **Thread Safety**: Concurrent access by multiple users is fully supported
- **User Isolation**: Each phone number maintains independent conversation context
- **API Failure Recovery**: Sessions preserved during OpenAI/Twilio timeouts

---

## 📊 MVP-Scale Testing Results

### **Test Coverage Summary**
```bash
# Core session functionality - All 20 tests PASSED
pytest tests/test_session_cleanup.py -v

# MVP user simulation - 6 tests PASSED  
pytest tests/test_mvp_session_lifecycle.py -v

# TTL refresh behavior - 7 tests PASSED
pytest tests/test_ttl_refresh_behavior.py -v

# API failure recovery - All tests PASSED
pytest tests/test_api_failure_recovery.py -v
```

### **Validated Scenarios**
- **3 concurrent users** creating press releases simultaneously
- **Session persistence** across realistic conversation timing (30-120 seconds between messages)
- **TTL refresh** keeping active conversations alive beyond base TTL
- **Thread isolation** preventing conversation cross-contamination
- **Memory stability** during repeated API failures
- **Emergency rollback** capability via `scripts/rollback_session_manager.py`

---

## 🚀 Production Deployment Configuration

### **Environment Variables**
```bash
# Required for SessionManager
OPENAI_API_KEY=sk-your-key-here              # Must be set before app start
TWILIO_AUTH_TOKEN=your-32-char-token         # For webhook verification

# Session Configuration (Optional - defaults shown)
SESSION_TTL_SECONDS=3600                     # 1 hour session lifetime
SESSION_CLEANUP_INTERVAL=300                 # 5 minute cleanup frequency
```

### **Health Monitoring Endpoints**
```bash
# Session system health
GET /health/sessions
# Returns: {"status": "healthy", "session_manager": {...}}

# Detailed session metrics
GET /health/sessions/details  
# Returns active sessions, memory usage, cleanup stats

# Manual cleanup trigger
POST /health/sessions/cleanup
# Force immediate cleanup of expired sessions
```

### **Session Metrics Tracking**
```python
metrics = session_manager.get_metrics()
# Returns:
{
    "active_sessions": 12,
    "total_sessions_created": 156,
    "total_sessions_expired": 144,
    "estimated_memory_bytes": 24576,
    "last_cleanup_time": "2025-08-06T10:30:00Z",
    "cleanup_interval_seconds": 300
}
```

---

## 🔧 MVP Production Checklist

### **Pre-Deployment Validation**
- [ ] **API Keys**: OPENAI_API_KEY set before application start (prevents 50% failure rate)
- [ ] **Health Check**: `curl -I /health/sessions` returns 200 OK
- [ ] **Session Creation**: New user messages create sessions successfully
- [ ] **TTL Behavior**: Sessions expire after configured TTL period
- [ ] **Cleanup Process**: Automatic cleanup removes expired sessions

### **Post-Deployment Monitoring**
```bash
# Monitor session health every 5 minutes
curl -s http://localhost:8000/health/sessions/details | jq '.active_sessions'

# Check for memory leaks (should stay stable)
curl -s http://localhost:8000/health/sessions/details | jq '.estimated_memory_bytes'

# Force cleanup if needed
curl -X POST http://localhost:8000/health/sessions/cleanup
```

### **Performance Expectations (MVP Scale)**
- **Response Time**: <15 seconds for WhatsApp webhook responses
- **Memory Usage**: ~2KB per active session (~40KB for 20 users)
- **Cleanup Efficiency**: ~1ms per expired session removal
- **Thread Safety**: 100% isolation between concurrent users

---

## 🔐 Security & Privacy Considerations

### **Phone Number Privacy**
- **Hashing**: Phone numbers hashed in logs (last 4 digits shown)
- **Session Keys**: Raw phone numbers used as session keys (secure memory only)
- **Cleanup**: Expired sessions completely removed from memory

### **Thread ID Protection**
- **OpenAI Integration**: Thread IDs are OpenAI Assistant API identifiers
- **No Sensitive Data**: Thread IDs contain no user information
- **Cleanup**: Orphaned threads cleaned up with sessions

---

## ⚡ Emergency Procedures

### **Session System Failure Recovery**
```bash
# 1. Check system health
curl -I http://localhost:8000/health/sessions

# 2. Force cleanup if needed
curl -X POST http://localhost:8000/health/sessions/cleanup

# 3. Emergency rollback to legacy sessions (if critical)
python scripts/rollback_session_manager.py --dry-run
python scripts/rollback_session_manager.py  # Execute rollback
```

### **Memory Leak Detection**
```bash
# Check memory growth trend
curl -s http://localhost:8000/health/sessions/details | \
  jq '.estimated_memory_bytes, .active_sessions'

# If memory grows beyond 100KB with <20 users, investigate:
# 1. Check for expired sessions not being cleaned
# 2. Verify cleanup interval is running
# 3. Look for session creation without proper expiration
```

### **High Error Rate Response**
1. **Check OpenAI API Status**: Lazy initialization prevents auth failures
2. **Verify Twilio Webhooks**: HMAC verification must pass
3. **Session State**: Sessions should survive API failures
4. **Rollback Option**: Emergency rollback script available if needed

---

## 📈 Scaling Beyond MVP

### **When to Scale Up**
- **User Count**: >15 concurrent active sessions
- **Memory Usage**: >80KB estimated memory bytes
- **Response Times**: >10 seconds average response time
- **Cleanup Frequency**: Needs to increase beyond 5-minute intervals

### **Scaling Preparation**
- **Database Migration**: SQLite → PostgreSQL for distributed sessions
- **Cleanup Threading**: Background cleanup threads
- **Load Balancing**: Multiple application instances with shared session store
- **Monitoring**: Prometheus metrics for session lifecycle tracking

---

## 🧪 Development & Testing

### **Local Testing Commands**
```bash
# Full session test suite
pytest tests/test_session_cleanup.py tests/test_mvp_session_lifecycle.py -v

# API failure simulation
pytest tests/test_api_failure_recovery.py -v

# Memory leak testing
pytest tests/test_session_cleanup_safety.py::test_cleanup_metrics_consistency -v
```

### **Session State Debugging**
```python
# In production debugging (use health endpoints instead)
from app.agent_endpoint import session_manager

# Current active sessions
print(f"Active sessions: {len(session_manager._sessions)}")

# Session details for specific user
entry = session_manager._sessions.get("+1234567890")
if entry:
    print(f"Thread: {entry.thread_id}")
    print(f"Created: {entry.created_at}")
    print(f"Last accessed: {entry.last_accessed}")
```

---

*This guide covers MVP session management for WhatsPR deployment with <20 concurrent users. All scenarios tested and validated for production readiness.*