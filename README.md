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

- Python 3.10+ (or Python 3.12 as shown in the local environment)
- Node.js 18+ / npm 10+ for the frontend
- `pip` for Python package installation

## Backend Setup

1. Open a terminal and change into the backend folder:

```powershell
cd backend
```

2. Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Start the backend API:

```powershell
python -m uvicorn server.api:app --host 127.0.0.1 --port 8000
```

### Optional backend launcher

The existing `backend/run_demo.py` can also be used, but it must be executed from the `backend/` folder and the internal Uvicorn target must point to `server.api:app`.

## Frontend Setup

1. Open a second terminal and change into the frontend folder:

```powershell
cd frontend
```

2. Install npm dependencies:

```powershell
npm install
```

3. Start the React development server:

```powershell
npm start
```

4. Open the UI in your browser at:

```text
http://localhost:3000
```

## Local Development Notes

- The frontend currently points to the local backend API at `http://127.0.0.1:8000` and the WebSocket at `ws://127.0.0.1:8000/ws`.
- The simulation mission is launched by calling the backend endpoint `/start_mission` from the React UI.
- Mission data is stored in `backend/detections.db`.

## Deployment Notes

- The React frontend can be deployed to Netlify or any static hosting service.
- The FastAPI backend must be deployed separately to a Python-capable host (Render, Railway, Fly, Heroku, Azure, Cloud Run, etc.).
- When deploying, update the frontend API base URL and WebSocket URL from `127.0.0.1` to your backend host.

### Example frontend environment variables

```env
REACT_APP_API_BASE_URL=https://your-backend.example.com
REACT_APP_WS_BASE_URL=wss://your-backend.example.com
```

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


