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