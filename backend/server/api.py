from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from server.database import DetectionDB
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

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
image_dir = os.path.join(base_dir, "insects")
metadata_file = os.path.join(base_dir, "insect_names.txt")

if os.path.isdir(image_dir):
    app.mount("/insects/images", StaticFiles(directory=image_dir), name="insects")

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

@app.get("/insects/list")
def list_insects():
    if not os.path.exists(metadata_file):
        return []

    images = {}
    if os.path.isdir(image_dir):
        for filename in os.listdir(image_dir):
            name, ext = os.path.splitext(filename)
            if ext.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                images[name] = filename

    results = []
    with open(metadata_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = [part.strip() for part in line.replace("\t", ",").split(",") if part.strip()]
            if len(parts) < 2:
                continue

            image_key = parts[0]
            insect_name = ",".join(parts[1:]).strip()
            filename = images.get(image_key)
            if not filename:
                for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                    candidate = f"{image_key}{ext}"
                    if candidate in images.values():
                        filename = candidate
                        break

            results.append({
                "id": image_key,
                "name": insect_name,
                "image": f"/insects/images/{filename}" if filename else None,
            })

    return results