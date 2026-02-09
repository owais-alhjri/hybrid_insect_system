import subprocess
import sys
import time
import os

def kill_zombies():
    if os.name == 'nt':
        # Kill any python process sitting on 8000
        os.system("for /f \"tokens=5\" %a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %a >nul 2>&1")

def banner():
    print("=" * 40)
    print(" 🛰️  OMAN AGRI-TECH SYSTEM  🛰️ ")
    print(" Backend  : http://127.0.0.1:8000")
    print(" Frontend : Ensure React is running on :3000")
    print("=" * 40)

if __name__ == "__main__":
    kill_zombies()
    time.sleep(1) # Wait for ports to clear
    banner()

    print("[INFO] Starting FastAPI Backend...")
    # Using python -m uvicorn allows better path resolution
    backend = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.api:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "info"
        ]
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN]")
    finally:
        backend.terminate()
        kill_zombies()