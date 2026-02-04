from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import DetectionDB
import config
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()
db = DetectionDB(config.DB_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dashboard_path = os.path.join(os.path.dirname(__file__), "..", "dashboard")
app.mount("/dashboard", StaticFiles(directory=dashboard_path), name="dashboard")

latest_event = {
    "status": "IDLE", # IDLE, SCANNING, VERIFYING
    "last_detection": None
}
@app.post("/update_live_view")
def update_live(data: dict):
    global latest_event
    
    # NEW LOGIC: If the incoming status is "AERIAL_SCANNING", 
    # it means a NEW mission just started. Reset the lock!
    if data.get("status") == "AERIAL_SCANNING":
        latest_event = data
        return {"status": "reset_and_updated"}

    # Keep the lock for other statuses
    if latest_event.get("status") == "FINISHED":
        return {"status": "locked"}
    
    latest_event = data
    return {"status": "ok"}
@app.post("/mission_complete")
def mission_complete():
    global latest_event
    latest_event = {"status": "FINISHED", "last_detection": None}
    return {"status": "ok"}

@app.get("/live_status")
def get_live_status():
    return latest_event

@app.get("/detections")
def get_detections():
    rows = db.conn.execute(
        "SELECT insect, confidence, source, timestamp "
        "FROM detections ORDER BY timestamp DESC LIMIT 50"
    ).fetchall()

    return [
        {
            "insect": r[0],
            "confidence": r[1],
            "source": r[2],
            "timestamp": r[3]
        }
        for r in rows
    ]
