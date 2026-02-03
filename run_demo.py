import subprocess
import sys
import time
import os

def banner():
    print("=" * 40)
    print(" Hybrid Cooperative Insect Detection ")
    print(" Mode      : DEMO (No Hardware)")
    print(" Model     : oman_insect_best.pt")
    print(" Classes   : 6 (Omani pests)")
    print("=" * 40)

banner()

# Start backend quietly
print("[INFO] Starting backend API...")
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.api:app"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(2)

print("[OK] Backend running at http://127.0.0.1:8000")
print("[OK] Dashboard available at: http://127.0.0.1:8000/dashboard/index.html")
print("-" * 40)
print(" Detecting insects...\n")

# Start detection engine
try:
    subprocess.call([sys.executable, "main.py"])
except KeyboardInterrupt:
    print("\n[STOPPED] System shutting down")
    backend.terminate()
