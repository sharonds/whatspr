# File Structure for Session Cleanup & Timeout Centralization

## New Files to Create

### Core Implementation Files

```
app/
├── session_manager.py          # Main SessionManager class
├── timeout_config.py           # TimeoutConfig and TimeoutManager classes
├── config/
│   ├── __init__.py
│   ├── session_config.py       # Session configuration dataclasses
│   └── timeout_profiles.py     # Timeout profiles (dev/staging/prod)
└── utils/
    ├── __init__.py
    └── memory_tracker.py       # Memory usage estimation utilities
```

### Test Files (Already Created)

```
tests/
├── test_session_cleanup.py     # Comprehensive session management tests
├── test_timeout_centralization.py  # Timeout configuration tests
├── integration/
│   ├── __init__.py
│   ├── test_session_integration.py  # End-to-end session tests
│   └── test_timeout_integration.py  # End-to-end timeout tests
└── performance/
    ├── __init__.py
    ├── test_memory_performance.py   # Memory usage tests
    └── test_timeout_performance.py  # Timeout performance tests
```

### Configuration Files

```
config/
├── session_settings.yaml       # Session cleanup configuration
├── timeout_profiles.yaml       # Timeout profiles for different environments
└── monitoring_config.yaml      # Monitoring and alerting configuration
```

### Documentation Files

```
docs/
├── session_cleanup_guide.md    # User guide for session management
├── timeout_configuration.md    # Timeout configuration documentation
├── migration_guide.md          # Migration from old system
└── troubleshooting.md          # Common issues and solutions
```

## Files to Modify

### Existing Files That Need Updates

```
app/agent_endpoint.py
├── Replace _sessions dict with SessionManager
├── Integrate TimeoutManager
├── Add backward compatibility flags
└── Update logging and monitoring

app/agent_runtime.py  
├── Replace hardcoded timeouts with TimeoutConfig
├── Update polling logic to use centralized config
├── Add timeout event tracking
└── Maintain backward compatibility

app/main.py
├── Initialize SessionManager and TimeoutManager
├── Add configuration loading
├── Setup monitoring and health checks
└── Add environment profile detection
```

### Configuration Files to Update

```
.env.example
├── Add SESSION_TTL_SECONDS
├── Add SESSION_CLEANUP_INTERVAL  
├── Add timeout configuration variables
└── Add profile selection variable

docker-compose.yml (if exists)
├── Add environment variables
├── Add health check endpoints
└── Add monitoring configuration

requirements.txt
├── Add any new dependencies
└── Update existing dependencies if needed
```

## Directory Organization Rationale

### 1. Separation of Concerns
- `session_manager.py`: Handles all session lifecycle management
- `timeout_config.py`: Manages all timeout configurations
- `config/`: Centralized configuration management
- `utils/`: Shared utilities and helper functions

### 2. Testability
- Each component has dedicated test files
- Integration tests verify component interaction
- Performance tests ensure scalability
- Test structure mirrors implementation structure

### 3. Maintainability
- Clear module boundaries
- Configuration separated from implementation
- Documentation co-located with implementation
- Migration guide for smooth transitions

### 4. Scalability
- Modular design allows independent scaling
- Configuration profiles support different environments
- Monitoring integration for production observability
- Memory tracking for resource management

## Implementation Order

### Phase 1: Core Infrastructure
1. `app/config/session_config.py` - Configuration dataclasses
2. `app/session_manager.py` - Core SessionManager implementation
3. `app/timeout_config.py` - TimeoutConfig and TimeoutManager
4. `app/utils/memory_tracker.py` - Memory estimation utilities

### Phase 2: Integration
1. Update `app/agent_endpoint.py` with SessionManager
2. Update `app/agent_runtime.py` with TimeoutConfig
3. Add configuration loading to `app/main.py`
4. Update environment and deployment configurations

### Phase 3: Testing & Validation
1. Run comprehensive test suite
2. Performance testing and benchmarking
3. Integration testing with existing functionality
4. Migration testing and validation

### Phase 4: Documentation & Deployment
1. Complete documentation and guides
2. Deployment scripts and configuration
3. Monitoring and alerting setup
4. Rollback procedures and safety measures