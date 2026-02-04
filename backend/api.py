from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import DetectionDB
import config

app = FastAPI()
db = DetectionDB(config.DB_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SINGLE SOURCE OF TRUTH
latest_event = {"status": "IDLE", "last_detection": None}

@app.get("/live_status")
def get_live_status():
    return latest_event

@app.post("/update_live_view")
def update_live(data: dict):
    global latest_event
    latest_event = data  # Always accept new updates
    return {"status": "ok"}

@app.post("/mission_complete")
def mission_complete():
    global latest_event
    latest_event = {"status": "FINISHED", "last_detection": None}
    return {"status": "ok"}

@app.post("/reset")
def reset_mission():
    db.conn.execute("DELETE FROM detections") # Wipe the logs
    db.conn.commit()
    global latest_event
    latest_event = {
        "status": "IDLE", 
        "last_detection": None
    }
    return {"status": "success"}

@app.get("/detections")
def get_detections():
    rows = db.conn.execute(
        "SELECT insect, confidence, source, timestamp "
        "FROM detections ORDER BY timestamp DESC LIMIT 50"
    ).fetchall()
    return [{"insect": r[0], "confidence": r[1], "source": r[2], "timestamp": r[3]} for r in rows]