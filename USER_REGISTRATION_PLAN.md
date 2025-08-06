# 🔒 WhatsPR User Registration & Access Control Implementation Plan

*Created: August 6, 2025 | Priority: High Security Feature*

## 🎯 **Problem Statement**

Currently, anyone with the WhatsApp number can access the WhatsPR bot. We need to implement user registration and access control to prevent unauthorized usage while maintaining the MVP's simplicity.

## 🚀 **Solution: PIN-based Registration System**

### **MVP Approach Selection**
**Chosen:** PIN-based Registration (15-minute implementation)
- ✅ Simple & secure for MVP deployment
- ✅ Admin controls via WhatsApp commands  
- ✅ File-based storage (no database required)
- ✅ Immediate security without complex infrastructure

**Alternatives Considered:**
- Phone Number Whitelist (too restrictive for growth)
- Admin Approval Flow (too complex for MVP)

---

## 📋 **Implementation Tasks**

### **Task 1: Create User Registry Module**

**File:** `app/user_registry.py`

```python
"""Simple file-based user registration for MVP deployment."""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Set
import time

class UserRegistry:
    """Simple file-based user registration for MVP deployment."""
    
    def __init__(self, data_file: str = "data/registered_users.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Load user data from file."""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.registered_users: Set[str] = set(data.get('users', []))
                self.pending_registrations: Dict[str, dict] = data.get('pending', {})
                self.admin_phones: Set[str] = set(data.get('admins', []))
        else:
            self.registered_users = set()
            self.pending_registrations = {}
            self.admin_phones = set()
            # Add your phone as first admin
            self.admin_phones.add("whatsapp:+31621366440")  # Your phone
            self._save_data()
    
    def _save_data(self):
        """Save user data to file."""
        data = {
            'users': list(self.registered_users),
            'pending': self.pending_registrations,
            'admins': list(self.admin_phones),
            'last_updated': time.time()
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, indent=2, fp=f)
    
    def is_registered(self, phone: str) -> bool:
        """Check if user is registered."""
        return phone in self.registered_users or phone in self.admin_phones
    
    def is_admin(self, phone: str) -> bool:
        """Check if user is admin."""
        return phone in self.admin_phones
    
    def start_registration(self, phone: str, pin: str) -> bool:
        """Start registration process with PIN."""
        # Simple PIN validation (you can make this more complex)
        correct_pin = "2024"  # MVP PIN - change this!
        
        if pin == correct_pin:
            self.registered_users.add(phone)
            # Remove from pending if exists
            self.pending_registrations.pop(phone, None)
            self._save_data()
            return True
        else:
            # Track failed attempts
            self.pending_registrations[phone] = {
                'failed_attempts': self.pending_registrations.get(phone, {}).get('failed_attempts', 0) + 1,
                'last_attempt': time.time()
            }
            self._save_data()
            return False
    
    def get_registration_status(self, phone: str) -> dict:
        """Get registration status for a phone."""
        return {
            'is_registered': self.is_registered(phone),
            'is_admin': self.is_admin(phone),
            'failed_attempts': self.pending_registrations.get(phone, {}).get('failed_attempts', 0),
            'total_registered_users': len(self.registered_users)
        }

# Global registry instance
user_registry = UserRegistry()
```

### **Task 2: Add Authentication Function**

**File:** `app/agent_endpoint.py` (Add after imports)

```python
# Add this import
from .user_registry import user_registry

# Add this function before @router.post("/agent"):
def check_user_access(phone: str, message: str) -> tuple[bool, Optional[str]]:
    """Check if user has access and handle registration.
    
    Returns:
        tuple: (has_access, response_message)
    """
    # Admin always has access
    if user_registry.is_admin(phone):
        return True, None
    
    # Registered user has access
    if user_registry.is_registered(phone):
        return True, None
    
    # Handle registration attempts
    if message.lower().startswith('register '):
        pin = message[9:].strip()  # Remove "register " prefix
        
        if user_registry.start_registration(phone, pin):
            return True, "✅ Welcome! You're now registered. What kind of announcement?\n  Press 1 for Funding round\n  Press 2 for Product launch\n  Press 3 for Partnership"
        else:
            attempts = user_registry.pending_registrations.get(phone, {}).get('failed_attempts', 1)
            return False, f"❌ Invalid PIN. Failed attempts: {attempts}\n\nTo register, send: register [PIN]\nContact admin for the PIN."
    
    # Show registration instructions
    return False, "🔒 Access Required\n\nTo use this bot, send: register [PIN]\n\nContact sharon@whatspr.com for the PIN.\n\n(This bot is for registered users only)"
```

### **Task 3: Update Agent Hook Function**

**File:** `app/agent_endpoint.py` (Modify existing `agent_hook` function)

**Location:** Add right after getting `phone`, `body`, and `clean` variables:

```python
@router.post("/agent")
async def agent_hook(request: Request):
    """Main agent endpoint with user authentication."""
    form = await request.form()
    phone = str(form.get("From", ""))
    body = str(form.get("Body", ""))
    clean = clean_message(body)
    
    if clean is None:
        return twiml("Please send text.")
    
    # Check user access BEFORE processing
    has_access, auth_response = check_user_access(phone, clean)
    if not has_access:
        log.info("access_denied", 
                phone_hash=phone[-4:] if phone else "none",
                message_preview=clean[:30] if clean else "none")
        return twiml(auth_response)
    
    # If auth_response exists, it means successful registration
    if auth_response:
        log.info("user_registered", 
                phone_hash=phone[-4:] if phone else "none")
        return twiml(auth_response)
    
    # Continue with existing logic...
    # (rest of your existing agent_hook code remains the same)
```

### **Task 4: Add Admin Commands**

**File:** `app/agent_endpoint.py` (Add after reset command handling)

**Location:** Add after the reset command check, before the main AI processing:

```python
# Handle admin commands (before main conversation processing)
if user_registry.is_admin(phone):
    if clean.lower().startswith('admin '):
        admin_cmd = clean[6:].strip().lower()
        
        if admin_cmd == 'stats':
            status = user_registry.get_registration_status(phone)
            return twiml(f"📊 Bot Stats:\n✅ Registered users: {status['total_registered_users']}\n👥 Admins: {len(user_registry.admin_phones)}\n📱 Your status: Admin")
        
        elif admin_cmd.startswith('add '):
            new_phone = admin_cmd[4:].strip()
            if new_phone.startswith('+') or new_phone.startswith('whatsapp:'):
                if not new_phone.startswith('whatsapp:'):
                    new_phone = f"whatsapp:{new_phone}"
                user_registry.registered_users.add(new_phone)
                user_registry._save_data()
                return twiml(f"✅ Added user: {new_phone[-4:]}")
            return twiml("❌ Invalid phone format. Use: admin add +1234567890")
        
        elif admin_cmd.startswith('remove '):
            target_phone = admin_cmd[7:].strip()
            if not target_phone.startswith('whatsapp:'):
                target_phone = f"whatsapp:{target_phone}"
            if target_phone in user_registry.registered_users:
                user_registry.registered_users.remove(target_phone)
                user_registry._save_data()
                return twiml(f"✅ Removed user: {target_phone[-4:]}")
            return twiml("❌ User not found")
        
        return twiml("Admin commands:\n• admin stats\n• admin add +1234567890\n• admin remove +1234567890")
```

### **Task 5: Setup Data Directory & Environment**

**Commands to run:**

```bash
# Create data directory
mkdir -p data

# Add to .gitignore
echo "# User registration data" >> .gitignore
echo "data/" >> .gitignore

# Add environment variables (optional)
echo "REGISTRATION_PIN=2024" >> .env
echo "ADMIN_PHONE=whatsapp:+31621366440" >> .env
```

### **Task 6: Create Tests**

**File:** `tests/test_user_registration.py`

```python
"""Tests for user registration system."""

import pytest
import tempfile
import os
from app.user_registry import UserRegistry

def test_user_registration_flow():
    """Test complete user registration flow."""
    # Use temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        registry = UserRegistry(data_file=temp_file)
        
        # Test admin is automatically added
        assert registry.is_admin("whatsapp:+31621366440")
        
        # Test new user registration
        test_phone = "whatsapp:+1234567890"
        assert not registry.is_registered(test_phone)
        
        # Test correct PIN
        assert registry.start_registration(test_phone, "2024")
        assert registry.is_registered(test_phone)
        
        # Test wrong PIN
        test_phone2 = "whatsapp:+9876543210"
        assert not registry.start_registration(test_phone2, "wrong")
        assert not registry.is_registered(test_phone2)
        
        # Test failed attempts tracking
        status = registry.get_registration_status(test_phone2)
        assert status['failed_attempts'] == 1
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
```

---

## 🧪 **Testing Plan**

### **Manual Testing Commands**

```bash
# 1. Test unauthorized access
curl -X POST http://localhost:8004/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=hello"
# Expected: Access denied message

# 2. Test successful registration
curl -X POST http://localhost:8004/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=register 2024"
# Expected: Welcome message

# 3. Test registered user access
curl -X POST http://localhost:8004/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=funding round"
# Expected: Normal bot response

# 4. Test admin commands
curl -X POST http://localhost:8004/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+31621366440&Body=admin stats"
# Expected: Registration statistics

# 5. Test failed registration
curl -X POST http://localhost:8004/agent \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+9999999999&Body=register wrong"
# Expected: Invalid PIN message
```

### **Automated Test Command**

```bash
# Run registration tests
pytest tests/test_user_registration.py -v
```

---

## 🔒 **Security Features**

✅ **PIN-based Authentication** - Simple but effective barrier  
✅ **Admin Controls** - Add/remove users, view statistics  
✅ **Failed Attempt Tracking** - Monitor registration attempts  
✅ **Privacy Protection** - Phone number hashing in logs  
✅ **Access Logging** - Track denied access attempts  
✅ **File-based Storage** - No database dependency for MVP  
✅ **Graceful Fallback** - Clear instructions for unauthorized users  

---

## 🚀 **Deployment Steps**

### **1. Development**
```bash
# Implement all files above
# Run tests: pytest tests/test_user_registration.py
# Test manually with curl commands
```

### **2. Production Deployment**
```bash
# Create data directory
mkdir -p data

# Update .env with secure PIN
echo "REGISTRATION_PIN=YOUR_SECURE_PIN_HERE" >> .env

# Deploy with existing process
# Test with real WhatsApp number
```

### **3. User Onboarding**
1. **Share PIN** with authorized users via secure channel
2. **Test registration** with a few users
3. **Monitor logs** for access denied attempts
4. **Use admin commands** to manage users

---

## 📊 **Success Metrics**

- ✅ **Unauthorized access blocked** - 100% of unregistered users denied
- ✅ **Registration flow works** - Users can register with correct PIN
- ✅ **Admin controls functional** - Can add/remove users via WhatsApp
- ✅ **No disruption to existing users** - Your phone continues to work
- ✅ **Logging visibility** - Can monitor access attempts

---

## 🔄 **Future Enhancements** (Post-MVP)

- **Database storage** for scalability
- **Multiple PIN levels** (user/admin)
- **Time-limited registrations**
- **User self-service unregister**
- **Registration analytics dashboard**
- **Webhook notifications** for new registrations

---

## 📋 **Implementation Checklist**

- [ ] Create `app/user_registry.py`
- [ ] Add import to `app/agent_endpoint.py`
- [ ] Add `check_user_access()` function
- [ ] Update `agent_hook()` with authentication
- [ ] Add admin commands section
- [ ] Create `data/` directory
- [ ] Update `.gitignore`
- [ ] Add environment variables
- [ ] Create `tests/test_user_registration.py`
- [ ] Run manual tests
- [ ] Run automated tests
- [ ] Deploy to production
- [ ] Test with real WhatsApp

---

**Implementation Time:** ~15-20 minutes for MVP version  
**Security Level:** Medium (sufficient for MVP, scalable for growth)  
**Maintenance:** Low (file-based, simple admin commands)

*This plan provides immediate security while maintaining MVP simplicity and scalability.*
