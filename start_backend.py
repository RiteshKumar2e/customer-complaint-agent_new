#!/usr/bin/env python
"""Start backend server properly"""
import os
import subprocess
import sys

# Get the path to the backend directory relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: folder is named 'customer-complaint-agent_new' but backend is inside 'backend'
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if os.path.exists(BACKEND_DIR):
    os.chdir(BACKEND_DIR)

# Render uses 0.0.0.0 and a provided $PORT
host = "0.0.0.0" if os.getenv("RENDER") else "127.0.0.1"
port = os.getenv("PORT", "8000")

subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", port])
