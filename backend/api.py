from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.database import DetectionDB
import config
import subprocess
import sys
import threading
import asyncio
import os
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()
mission_process = None
mission_lock = threading.Lock()

# FIX: Only instantiate FastAPI once
app = FastAPI()

# FIX: Only add Middleware once with permissive settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DetectionDB(config.DB_NAME)
latest_event = {"status": "IDLE", "last_detection": None}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json(latest_event)
    try:
        while True:
            await asyncio.sleep(1) # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/live_status")
def get_live_status():
    return latest_event

@app.post("/update_live_view")
async def update_live(data: dict):
    global latest_event
    
    # FIX: Safety check before accessing dictionary keys
    if data.get("last_detection") and isinstance(data["last_detection"], dict):
        if "timestamp" not in data["last_detection"]:
            data["last_detection"]["timestamp"] = datetime.now().isoformat()
        
    latest_event = data
    await manager.broadcast(latest_event)
    return {"status": "ok"}

@app.post("/mission_complete")
async def mission_complete():
    global latest_event
    latest_event = {"status": "FINISHED", "last_detection": None}
    await manager.broadcast(latest_event)
    return {"status": "ok"}

@app.post("/reset")
async def reset_mission():
    try:
        db.conn.execute("DELETE FROM detections")
        db.conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")

    global latest_event
    latest_event = {"status": "IDLE", "last_detection": None}
    await manager.broadcast(latest_event)
    return {"status": "success"}

@app.get("/detections")
def get_detections():
    try:
        rows = db.conn.execute(
            "SELECT insect, confidence, source, timestamp "
            "FROM detections ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
        return [{"insect": r[0], "confidence": r[1], "source": r[2], "timestamp": r[3]} for r in rows]
    except:
        return []

@app.post("/start_mission")
async def start_mission():
    global mission_process
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main_script = os.path.join(base_dir, "main.py")

    with mission_lock:
        if mission_process and mission_process.poll() is None:
            return {"status": "already_running"}

        # Clear DB
        db.conn.execute("DELETE FROM detections")
        db.conn.commit()

        try:
            mission_process = subprocess.Popen(
                [sys.executable, main_script],
                cwd=base_dir,
                stdout=None, 
                stderr=None
            )
            print(f"🚀 Mission started at: {main_script}")
        except Exception as e:
            print(f"❌ Failed to launch: {e}")
            return {"status": "error", "message": str(e)}

        return {"status": "started"}

@app.post("/stop_mission")
async def stop_mission():
    global mission_process, latest_event

    with mission_lock:
        if mission_process and mission_process.poll() is None:
            mission_process.terminate()
            mission_process = None

        latest_event = {"status": "STOPPED", "last_detection": None}
        await manager.broadcast(latest_event)

    return {"status": "stopped"}