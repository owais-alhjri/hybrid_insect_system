import time, config
from ai.detector import InsectDetector
from mock.mock_drone import MockDrone
from mock.mock_tank import MockTank
from controller.coordinator import Coordinator
from backend.database import DetectionDB
import requests

# Initialize Components
detector = InsectDetector(config.MODEL_PATH, config.IMG_SIZE, config.DRONE_CONF_THRESHOLD)
db = DetectionDB(config.DB_NAME)
drone = MockDrone(detector)
tank = MockTank(detector)
brain = Coordinator(db) 

print("[SYSTEM] Simulation Initialized. Waiting for mission start...")

try:
    while True:
        # 1. Drone Scan
        drone_detections, location_index = drone.scan()
        if location_index == -1: break 
        
        # ONLY call brain.process. Do NOT call requests.post manually here.
        brain.process(drone_detections, "AERIAL")
        time.sleep(1) 

        # 2. Tank Verify
        tank_detections = tank.verify(location_index)
        
        # ONLY call brain.process.
        brain.process(tank_detections, "GROUND")
        time.sleep(2)

    requests.post("http://127.0.0.1:8000/mission_complete")
except KeyboardInterrupt:
    print("\n[STOPPED]")