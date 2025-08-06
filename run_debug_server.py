#!/usr/bin/env python3
"""Run server and capture debug output while testing."""

import subprocess
import time
import requests
import threading
import sys
import os
from pathlib import Path

def test_after_delay():
    """Test the server after a short delay."""
    time.sleep(3)  # Wait for server to start
    
    print("\n" + "="*50)
    print("🧪 TESTING WITH DEBUG OUTPUT")
    print("="*50)
    
    try:
        # Test reset first  
        print("Testing reset...")
        resp = requests.post('http://localhost:8004/agent', 
            data={'From': '+15551234567', 'Body': 'reset', 'MessageSid': 'DBG1', 'NumMedia': '0'},
            timeout=5
        )
        print(f"Reset: {resp.status_code} - {'✅' if 'announcement' in resp.text else '❌'}")
        
        time.sleep(1)
        
        # Test menu selection (the failing one)
        print("Testing menu selection '1'...")
        resp = requests.post('http://localhost:8004/agent',
            data={'From': '+15551234567', 'Body': '1', 'MessageSid': 'DBG2', 'NumMedia': '0'},
            timeout=20
        )
        print(f"Menu: {resp.status_code} - {'✅' if 'Oops' not in resp.text else '❌'}")
        print(f"Response: {resp.text[:100]}...")
        
    except Exception as e:
        print(f"Test failed: {e}")
    
    print("="*50)

if __name__ == "__main__":
    # Start test in background thread
    test_thread = threading.Thread(target=test_after_delay)
    test_thread.daemon = True
    test_thread.start()
    
    # Run server in foreground to see debug output
    print("🚀 Starting server with debug output visible...")
    print("Server will show actual exception details when error occurs")
    print("="*70)
    
    try:
        # Run server and capture output
        result = subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", "--reload", "--port", "8004"
        ], cwd=Path(__file__).parent, capture_output=False, text=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server failed: {e}")