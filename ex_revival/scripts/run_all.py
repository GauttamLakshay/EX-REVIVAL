#!/usr/bin/env python3
"""
EX REVIVAL - Service Orchestration Script
Runs the FastAPI Backend and Chatterbox Voice Service simultaneously.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def main():
    print("=" * 60)
    print(" EX REVIVAL -- Launching Backend & Voice Service")
    print("=" * 60)

    backend_dir = ROOT_DIR / "backend"
    voice_dir = ROOT_DIR / "voice_service"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    # 1. Start Voice Service on port 8001
    print("Starting Chatterbox Voice Service on http://localhost:8001 ...")
    voice_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "voice_service.app.main:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=str(ROOT_DIR),
        env=env,
    )

    # 2. Start Backend Orchestrator on port 8000
    print("Starting FastAPI Orchestrator on http://localhost:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(backend_dir),
        env=env,
    )

    print("\nServices running:")
    print("  * API Docs (Swagger): http://localhost:8000/docs")
    print("  * API Health:         http://localhost:8000/api/v1/health")
    print("  * Voice Service:      http://localhost:8001/health")
    print("\nPress Ctrl+C to terminate all services.\n")


    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
        backend_proc.terminate()
        voice_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()
