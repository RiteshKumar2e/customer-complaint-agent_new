#!/usr/bin/env python
"""Start backend server properly"""
import os
import subprocess
import sys

os.chdir(r"c:\Users\anmol\OneDrive\Desktop\customer-complaint-agent\backend")
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
