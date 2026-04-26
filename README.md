# Hybrid Insect System

A hybrid autonomous insect detection system with a FastAPI backend and a React frontend.

## Project Overview

- `backend/` contains the Python simulation, FastAPI server, object detection integration, and local SQLite storage.
- `frontend/` contains the React dashboard and live-status UI.

The system is designed for local development and testing of a simulated drone + tank mission flow.

## Repository Structure

- `backend/`
  - `run_demo.py` - helper script to launch the FastAPI backend.
  - `server/api.py` - FastAPI app with WebSocket and mission control endpoints.
  - `main.py` - mission simulator that runs the drone and tank detection loop.
  - `config.py` - model, image source, and database configuration.
  - `requirements.txt` - Python dependencies for the backend.
  - `detections.db` - SQLite database file created at runtime.
- `frontend/`
  - `package.json` - React app dependencies and scripts.
  - `src/` - React source code and UI logic.
  - `public/` - static frontend assets.

## Requirements

- Python 3.10+
- Node.js 18+ and npm
- `pip` for backend dependencies

## Quick Start

1. Open a terminal for the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_demo.py
```

2. Open another terminal for the frontend:

```powershell
cd frontend
npm install
npm start
```

3. Open the app in your browser:

```text
http://localhost:3000
```

## Notes

- The frontend uses the backend API at `http://127.0.0.1:8000`.
- The backend WebSocket URL is `ws://127.0.0.1:8000/ws`.
- Insect images and metadata are loaded from the backend and shown on the `INSECTS` page.
- If you do not want to use the virtual environment, run `python -m pip install -r requirements.txt` from the `backend/` folder.

## Useful Commands

From `backend/`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn server.api:app --host 127.0.0.1 --port 8000
```

From `frontend/`:

```powershell
npm install
npm start
```

## Troubleshooting

- If backend import errors occur, make sure you are running commands from the `backend/` folder.
- If the frontend cannot connect, ensure the FastAPI server is running on port `8000`.
- If you want to host only the frontend on Netlify, the backend must still run on a separate service and the frontend must use that deployed backend URL.


