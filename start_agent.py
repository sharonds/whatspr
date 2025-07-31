#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Load environment variables from .env file
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().strip().split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            os.environ[key] = value

# Set agent mode
os.environ['AGENT_MODE'] = 'true'

# Now start uvicorn
import uvicorn
if __name__ == "__main__":
    uvicorn.run("agent_app:app", host="127.0.0.1", port=8000, reload=True)
