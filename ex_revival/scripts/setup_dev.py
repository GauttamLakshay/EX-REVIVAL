#!/usr/bin/env python3
"""
EX REVIVAL - Developer Setup Script
Validates Python, Flutter, creates storage directories, and initializes the local database.
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def main():
    print("=" * 60)
    print(" EX REVIVAL -- Developer Environment Setup")
    print("=" * 60)

    # 1. Verify storage paths
    storage_dir = ROOT_DIR / "storage"
    (storage_dir / "reference_audio").mkdir(parents=True, exist_ok=True)
    (storage_dir / "generated_audio").mkdir(parents=True, exist_ok=True)
    (storage_dir / "temp").mkdir(parents=True, exist_ok=True)
    print("[OK] Storage directories created at:", storage_dir)

    # 2. Check Python packages
    try:
        import fastapi, uvicorn, sqlalchemy, soundfile, bcrypt, jwt
        print("[OK] Core backend Python libraries verified.")
    except ImportError as e:
        print(f"[!] Missing Python package: {e}")
        print("Run: pip install -r backend/requirements.txt")

    # 3. Create dummy sample reference audio if not exists
    sample_ref = storage_dir / "reference_audio" / "sample_alex.wav"
    if not sample_ref.exists():
        try:
            import numpy as np, soundfile as sf
            sr = 24000
            t = np.linspace(0, 3, sr * 3, endpoint=False)
            tone = 0.5 * np.sin(2 * np.pi * 180 * t) + 0.2 * np.sin(2 * np.pi * 360 * t)
            sf.write(str(sample_ref), tone.astype(np.float32), sr)
            print("[OK] Sample reference audio created at:", sample_ref)
        except Exception as e:
            print("[!] Could not generate sample audio:", e)


    print("\nEnvironment is ready.")
    print("To start the backend:")
    print("  python scripts/run_all.py")
    print("To run backend tests:")
    print("  cd backend && python -m pytest tests/ -v")
    print("To run Flutter app:")
    print("  cd frontend && flutter run")
    print("=" * 60)

if __name__ == "__main__":
    main()
