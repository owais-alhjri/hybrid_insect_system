import time
import requests
from ai.detector import InsectDetector
from mock.mock_drone import MockDrone
from mock.mock_tank import MockTank
from controller.coordinator import Coordinator
from backend.database import DetectionDB
import config

# --- NEW: RESET DASHBOARD ON STARTUP ---
try:
    requests.post("http://127.0.0.1:8000/reset")
    print("🧹 Dashboard Reset.")
except:
    pass 

# Initialize System
detector = InsectDetector(config.MODEL_PATH, config.IMG_SIZE, config.DRONE_CONF_THRESHOLD)
db = DetectionDB(config.DB_NAME)
drone = MockDrone(detector)
tank = MockTank(detector)
brain = Coordinator(db) 

print("🚀 Starting Mission...")

try:
    while True:
        drone_detections, location_index = drone.scan()
        if location_index == -1: break 
            
        print(f"\n--- SECTOR {location_index + 1} ---")
        brain.process(drone_detections, "AERIAL")
        
        time.sleep(2) 
        tank_detections = tank.verify(location_index)
        brain.process(tank_detections, "GROUND")
        time.sleep(5) 

    print("\n✅ MISSION COMPLETE.")
    requests.post("http://127.0.0.1:8000/mission_complete")

except KeyboardInterrupt:
    print("\n[STOPPED]")