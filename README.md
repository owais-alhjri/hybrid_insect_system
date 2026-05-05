# Hybrid Insect Detection System — OMAN AGRI-TECH

An automated insect detection system using a simulator-based hybrid model that replaces a physical drone–tank concept with a fully software-driven solution. The system integrates a React dashboard, a FastAPI backend, WebSocket real-time communication, a YOLOv8s AI model, and an SQLite database.

## Features

- 🚁 **Drone + Tank Simulation** — simulated aerial and ground unit detection with real-time live feed
- 🎥 **Video Detection** — upload a video and watch frame-by-frame insect detection in real time
- 📷 **Live Camera Detection** — scan a QR code with your phone to stream live camera frames for detection via WebRTC
- 🦟 **Insect Library** — browse all detectable insects with images and names
- 📊 **Real-time Dashboard** — WebSocket-powered live status, detection logs, and confidence scores
- 🗄️ **Detection Logging** — all detections saved to SQLite with source, timestamp, and confidence

## Detectable Insects

- Tuta Absoluta
- Longhorn Beetle
- White Grubs
- Weevil
- Armyworm
- Rhynchophorus Ferrugineus
- Locust

## Project Structure

```
hybrid_insect_system/
├── backend/
│   ├── run_demo.py              # Launch script — starts backend with HTTPS
│   ├── main.py                  # Mission simulator (drone + tank detection loop)
│   ├── config.py                # Model path, image source, DB configuration
│   ├── requirements.txt         # Python dependencies
│   ├── ssl/                     # Auto-generated self-signed SSL certificates
│   ├── insects/                 # Insect reference images
│   ├── insect_names.txt         # Insect name metadata
│   ├── detections.db            # SQLite database (created at runtime)
│   ├── server/
│   │   ├── api.py               # FastAPI app — WebSocket, WebRTC, video, camera endpoints
│   │   └── database.py          # SQLite detection logging
│   ├── ai/
│   │   └── detector.py          # YOLOv8s inference wrapper
│   ├── controller/
│   │   └── coordinator.py       # Mission coordinator — scan, verify, report workflow
│   └── mock/
│       ├── mock_drone.py        # Simulated aerial unit
│       └── mock_tank.py         # Simulated ground unit
└── frontend/
    ├── package.json             # React dependencies
    ├── src/
    │   ├── App.js               # Main dashboard — all pages and WebSocket logic
    │   └── command-center.css   # Dashboard styles
    └── public/                  # Static assets
```

## Requirements

- Python 3.10+
- Node.js 18+ and npm
- Both laptop and phone on the same WiFi network (for live camera feature)

## Quick Start

**1. Backend:**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_demo.py
```

The backend starts on `https://<your-local-ip>:8000`

> **First time only:** Open `https://127.0.0.1:8000` in your browser and accept the security warning. Do the same on your phone at `https://<local-ip>:8000` to enable the live camera feature.

**2. Frontend:**

```powershell
cd frontend
npm install
npm start
```

**3. Open the dashboard:**
http://localhost:3000

## How to Use

| Feature | How |
|---|---|
| Start mission | Click **START MISSION** on the dashboard |
| Stop mission | Click **STOP** |
| Video detection | Click **VIDEO** → upload a video file → click Start |
| Live camera | Click **CAMERA** → scan QR with phone → tap Start Camera |
| Insect library | Click **INSECTS** |
| Reset/clear logs | Click **REBOOT** |

## Tech Stack

| Layer | Technology |
|---|---|
| AI Model | YOLOv8s (Ultralytics) |
| Backend | FastAPI, Uvicorn |
| Real-time | WebSocket |
| Live Camera | WebRTC (aiortc) |
| Frontend | React |
| Database | SQLite |
| SSL | Self-signed cert (cryptography library) |

## Deactivate virtual environment

```powershell
deactivate
```