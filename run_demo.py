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
    print(" Backend  : http://127.0.0.1:8000 (ACTIVE)")
    print(" Simulation: Running main.py")
    print("=" * 40)

if __name__ == "__main__":
    kill_zombies()
    banner()

    # 1. Start Backend and KEEP IT RUNNING
    print("[INFO] Starting FastAPI Backend...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(3)

    try:
        while True:
            print("\n[READY] Starting New Mission Simulation...")
            # 2. Run the simulation
            subprocess.call([sys.executable, "main.py"])
            
            print("\n[WAITING] Mission Finished. Dashboard is still LIVE.")
            print("[ACTION] Press 'REBOOT' in browser or 'Ctrl+C' here to stop all.")
            
            # This loop keeps the script alive so the backend doesn't die
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping all services...")
    finally:
        backend.terminate()
        kill_zombies()