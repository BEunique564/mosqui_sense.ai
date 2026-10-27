"""
MosquiSense AI — One-click startup script for Sadar Cantt demo.

Usage:
    python scripts/run_demo.py

Starts:
    - Backend FastAPI server on port 8000
    - Frontend Next.js dev server on port 3000
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   🦟 MosquiSense AI — Sadar Cantt, Lucknow     ║
    ║   Real-time Mosquito Outbreak Prediction        ║
    ║   MOSDAC Satellite + AI Ensemble                ║
    ╚══════════════════════════════════════════════════╝
    """)

    # Check Python version
    if sys.version_info < (3, 11):
        print("ERROR: Python 3.11+ required")
        sys.exit(1)

    # Check if .env exists
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("WARNING: .env not found. Using defaults.")
        print("  Copy .env.example to .env and configure your API keys.")

    print("[1/3] Installing Python dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q",
         "fastapi", "uvicorn[standard]", "pydantic", "pydantic-settings",
         "httpx", "numpy"],
        check=True,
    )

    print("[2/3] Installing frontend dependencies...")
    frontend_dir = ROOT / "frontend"
    if (frontend_dir / "node_modules").exists():
        print("  node_modules exists, skipping npm install")
    else:
        subprocess.run(["npm", "install"], cwd=str(frontend_dir), check=True)

    print("[3/3] Starting servers...\n")

    # Start backend
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.standalone_server:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(ROOT),
    )

    # Wait for backend to start
    time.sleep(3)

    # Start frontend
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(frontend_dir),
    )

    print("    Backend:  http://localhost:8000/docs")
    print("    Frontend: http://localhost:3000")
    print("    Health:   http://localhost:8000/health")
    print("    Dashboard API: http://localhost:8000/v1/dashboard/summary\n")
    print("    Press Ctrl+C to stop both servers.\n")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")


if __name__ == "__main__":
    main()
