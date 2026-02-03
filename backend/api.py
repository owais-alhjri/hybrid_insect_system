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
