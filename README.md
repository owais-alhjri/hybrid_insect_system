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
4. to exec .venv ```deactivate```
