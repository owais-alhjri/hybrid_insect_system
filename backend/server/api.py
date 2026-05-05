from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from server.database import DetectionDB
from ai.detector import InsectDetector
import config
import subprocess
import sys
import threading
import asyncio
import os
import socket
import cv2
import numpy as np
import qrcode
import tempfile
from io import BytesIO
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRelay
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
pcs = set()
relay = MediaRelay()
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

class DetectionVideoTrack:
    def __init__(self, track, source="camera"):
        self.track = track
        self.source = source
        self.frame_count = 0
        self.DETECT_EVERY = 45
        self.running = True

    async def start(self):
        while self.running:
            try:
                frame = await asyncio.wait_for(self.track.recv(), timeout=15.0)
                self.frame_count += 1

                if self.frame_count % self.DETECT_EVERY != 0:
                    continue

                img = frame.to_ndarray(format="bgr24")


                ## if you have GPU delete this
                img = cv2.resize(img, (320, 240))

                ## if you have strong CPU but no GPU use this
                ## img = cv2.resize(img, (640x480))


                loop = asyncio.get_event_loop()
                detections = await loop.run_in_executor(
                    None, video_detector.detect, img, "camera"
                )

                det = detections[0]

                if det.get("found"):
                    db.insert(det)
                    await manager.broadcast({
                        "status": "CAMERA_PROCESSING",
                        "last_detection": {**det, "source": "camera"},
                    })
                elif self.frame_count % self.DETECT_EVERY == 0:
                    # Send frame image even when nothing detected so dashboard shows live feed
                    await manager.broadcast({
                        "status": "CAMERA_PROCESSING",
                        "last_detection": {
                            **det,
                            "source": "camera",
                            "image": det.get("image") or det.get("raw_image"),
                        },
                    })

            except asyncio.TimeoutError:
                print("[WEBRTC] Frame timeout — connection dropped")
                break
            except Exception as e:
                print(f"[WEBRTC] Frame error: {e}")
                break

        await manager.broadcast({
            "status": "CAMERA_FINISHED",
            "last_detection": None
        })

    def stop(self):
        self.running = False

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
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as inner_error:
                print(f"[WS] receive error: {inner_error}")
                break
    finally:
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

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"

CAMERA_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Live Camera Detection</title>
  <style>
    body { margin:0; font-family:system-ui, sans-serif; background:#0b1120; color:#f8fafc; display:flex; min-height:100vh; align-items:center; justify-content:center; }
    .page { width:min(100%, 480px); padding:24px; }
    h1 { margin:0 0 12px; font-size:1.8rem; }
    p { margin:0 0 12px; color:#cbd5e1; }
    .status { margin:0 0 16px; display:flex; gap:12px; align-items:center; }
    video { width:100%; border-radius:18px; background:#000; }
    .info { margin-top:14px; font-size:0.95rem; color:#94a3b8; }
    .label { font-weight:700; color:#f8fafc; }
  </style>
</head>
<body>
  <div class=\"page\">
    <h1>Live Camera Detection</h1>
    <div class=\"status\"><span id=\"connection\">Connecting...</span><span id=\"message\"></span></div>
    <video id=\"cameraVideo\" autoplay playsinline muted></video>
    <canvas id=\"captureCanvas\" width=\"640\" height=\"480\" style=\"display:none;\"></canvas>
<button id="stopBtn" onclick="stopCamera()" disabled style="margin-top:16px; width:100%; padding:14px; background:#ef4444; color:#fff; border:none; border-radius:12px; font-size:1rem; font-weight:700; cursor:pointer; opacity:0.4;">
      Stop Camera
    </button>
    <button id="startBtn" onclick="startCamera()" style="margin-top:10px; width:100%; padding:14px; background:#22c55e; color:#fff; border:none; border-radius:12px; font-size:1rem; font-weight:700; cursor:pointer;">
      Start Camera
    </button>
  </div>
  <script>
    let pc = null;
    let stream = null;
    const statusEl = document.getElementById('connection');
    const messageEl = document.getElementById('message');
    const localVideo = document.getElementById('cameraVideo');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    function setStatus(text) { statusEl.textContent = text; }
    function setMessage(text) { messageEl.textContent = text; }
    function setButtons(running) {
      startBtn.disabled = running;
      startBtn.style.opacity = running ? '0.4' : '1';
      stopBtn.disabled = !running;
      stopBtn.style.opacity = running ? '1' : '0.4';
    }

    function getUserMedia(constraints) {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        return navigator.mediaDevices.getUserMedia(constraints);
      }

      const legacyGetUserMedia =
        navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia ||
        navigator.msGetUserMedia;

      if (legacyGetUserMedia) {
        return new Promise((resolve, reject) => {
          legacyGetUserMedia.call(navigator, constraints, resolve, reject);
        });
      }

      return Promise.reject(
        new Error(
          'Camera access is not available in this browser. Use a modern browser with WebRTC support.'
        )
      );
    }

async function startCamera() {
  setStatus('Requesting camera...');
  setButtons(true);
  setMessage('');

  try {
    stream = await getUserMedia({
      video: { facingMode: 'environment' },
      audio: false,
    });

    localVideo.srcObject = stream;

    const PeerConnection =
      window.RTCPeerConnection ||
      window.webkitRTCPeerConnection ||
      window.mozRTCPeerConnection;

    if (!PeerConnection) {
      throw new Error('WebRTC is not supported by this browser.');
    }

pc = new PeerConnection({
  iceServers: [],
});

pc.onconnectionstatechange = () => {
  setStatus('State: ' + pc.connectionState);
  if (pc.connectionState === 'connected') {
    setStatus('Streaming...');
    setButtons(true);
  } else if (pc.connectionState === 'failed' || pc.connectionState === 'closed') {
    setStatus('Connection lost');
    setButtons(false);
  }
};

    stream.getTracks().forEach((track) => pc.addTrack(track, stream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    // Wait for ICE gathering to complete before sending offer
    await new Promise((resolve) => {
      if (pc.iceGatheringState === 'complete') {
        resolve();
      } else {
        pc.addEventListener('icegatheringstatechange', () => {
          if (pc.iceGatheringState === 'complete') resolve();
        });
        // Fallback timeout in case gathering takes too long
        setTimeout(resolve, 8000);
      }
    });

    setStatus('Connecting to backend...');

    const response = await fetch(`https://{host}:8000/webrtc/offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sdp: pc.localDescription.sdp,
        type: pc.localDescription.type
      }),
    });

    const answer = await response.json();
    await pc.setRemoteDescription(new RTCSessionDescription(answer));

    setStatus('Streaming...');
  } catch (err) {
    setStatus('Error: ' + (err.message || err));
    setButtons(false);
  }
}

    function stopCamera() {
      if (pc) {
        pc.close();
        pc = null;
      }
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        stream = null;
      }
      localVideo.srcObject = null;
      setStatus('Stopped');
      setButtons(false);
    }

    window.addEventListener('beforeunload', stopCamera);
  </script>
</body>
</html>
"""

@app.get("/camera")
async def camera_page(request: Request):
    host = get_local_ip()
    content = CAMERA_PAGE_TEMPLATE.replace("{host}", host)
    return HTMLResponse(content=content, status_code=200)

@app.get("/camera-qr")
async def camera_qr(request: Request):
    host = get_local_ip()
    camera_host = f"https://{host}:8000"
    camera_url = f"{camera_host}/camera"
    img = qrcode.make(camera_url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")

@app.post("/webrtc/offer")
async def webrtc_offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"[WEBRTC] Connection state: {pc.connectionState}")
        if pc.connectionState in ["failed", "closed", "disconnected"]:
            if hasattr(pc, '_detector'):
                pc._detector.stop()
            await pc.close()
            pcs.discard(pc)
            await manager.broadcast({
                "status": "CAMERA_FINISHED",
                "last_detection": None
            })

    @pc.on("track")
    def on_track(track):
        print(f"[WEBRTC] Track received: kind={track.kind}")
        if track.kind == "video":
            detector = DetectionVideoTrack(relay.subscribe(track))
            pc._detector = detector
            asyncio.ensure_future(detector.start())

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
@app.on_event("shutdown")
async def on_shutdown():
    await asyncio.gather(*[pc.close() for pc in pcs], return_exceptions=True)
    pcs.clear()


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