from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from server.database import DetectionDB
from ai.detector import InsectDetector
import config
import subprocess
import sys
import threading
import asyncio
import os
import cv2
import tempfile
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

FRAME_SKIP = 3  # process 1 out of every 3 frames

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

video_detector = InsectDetector(config.MODEL_PATH, config.IMG_SIZE, config.DRONE_CONF_THRESHOLD)
video_processing = False
video_task = None
video_stop_requested = False
video_lock = threading.Lock()

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

async def process_video_file(file_path: str):
    global latest_event, video_processing, video_task, video_stop_requested

    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        latest_event = {"status": "VIDEO_ERROR", "last_detection": None}
        await manager.broadcast(latest_event)
        with video_lock:
            video_processing = False
            video_task = None
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_index = 0

    try:
        while True:
            if video_stop_requested:
                latest_event = {"status": "VIDEO_STOPPED", "last_detection": None}
                await manager.broadcast(latest_event)
                return

            success, frame = cap.read()
            if not success:
                break
            if frame_index % FRAME_SKIP != 0:
                frame_index += 1
                continue
            loop = asyncio.get_event_loop()
            detections = await loop.run_in_executor(None, video_detector.detect, frame, "video")
            if detections and detections[0].get("found"):
                for d in detections:
                    db.insert(d)

            progress = None
            if total_frames > 0:
                progress = min(100, round(((frame_index + 1) / total_frames) * 100))

            latest_event = {
                "status": "VIDEO_PROCESSING",
                "last_detection": {
                    **detections[0],
                    "source": "video",
                    "progress": progress,
                    "frame": frame_index + 1,
                },
            }
            await manager.broadcast(latest_event)
            frame_index += 1

        latest_event = {"status": "VIDEO_FINISHED", "last_detection": None}
        await manager.broadcast(latest_event)
    except asyncio.CancelledError:
        latest_event = {"status": "VIDEO_STOPPED", "last_detection": None}
        await manager.broadcast(latest_event)
        raise
    finally:
        cap.release()
        with video_lock:
            video_processing = False
            video_task = None
        try:
            os.remove(file_path)
        except Exception:
            pass

@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    global latest_event, video_processing, video_task, video_stop_requested

    with video_lock:
        if video_processing:
            return {"status": "busy", "message": "Video processing already in progress."}
        video_processing = True
        video_stop_requested = False
        video_task = None

    suffix = os.path.splitext(file.filename)[1] or ".mp4"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp_file.write(await file.read())
        temp_file.flush()
        temp_file.close()
    except Exception as exc:
        temp_file.close()
        try:
            os.unlink(temp_file.name)
        except Exception:
            pass
        with video_lock:
            video_processing = False
        return {"status": "error", "message": str(exc)}

    latest_event = {"status": "VIDEO_PROCESSING", "last_detection": None}
    await manager.broadcast(latest_event)
    with video_lock:
        video_task = asyncio.create_task(process_video_file(temp_file.name))

    return {"status": "started"}

@app.post("/stop_video")
async def stop_video():
    global latest_event, video_processing, video_task, video_stop_requested

    with video_lock:
        if not video_processing or video_task is None:
            return {"status": "no_video", "message": "No video is processing."}
        video_stop_requested = True
        task = video_task

    try:
        task.cancel()
    except Exception:
        pass

    latest_event = {"status": "VIDEO_STOPPED", "last_detection": None}
    await manager.broadcast(latest_event)
    return {"status": "stopped"}

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