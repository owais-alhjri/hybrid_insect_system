import time
import requests # Move this to the top
from ai.detector import InsectDetector
from mock.mock_drone import MockDrone
from mock.mock_tank import MockTank
from controller.coordinator import Coordinator
from backend.database import DetectionDB
import config

# Initialize System
detector = InsectDetector(
    config.MODEL_PATH,
    config.IMG_SIZE,
    config.DRONE_CONF_THRESHOLD
)

db = DetectionDB(config.DB_NAME)
drone = MockDrone(detector)
tank = MockTank(detector)
brain = Coordinator(db) 

print("🚀 Hybrid Insect Detection (Sequential Mode)")
print(f"   Aerial Folder: {config.DRONE_IMG_PATH}")
print(f"   Ground Folder: {config.TANK_IMG_PATH}")
print("-" * 40)

try:
    while True:
        drone_detections, location_index = drone.scan()
        
        if location_index == -1: 
            break # Just exit the loop
            
        print(f"\n--- SECTOR {location_index + 1} START ---")
        brain.process(drone_detections, "AERIAL")
        
        print("   >> Signal sent to Ground Unit...")
        time.sleep(2) 

        tank_detections = tank.verify(location_index)
        brain.process(tank_detections, "GROUND")

        print("-" * 40)
        time.sleep(5) 

    # --- THIS PART IS NOW OUTSIDE THE WHILE LOOP ---
    print("\n✅ MISSION COMPLETE. Sending final signal...")
    time.sleep(2) # Wait for any pending coordinator updates to finish
    try:
        requests.post("http://127.0.0.1:8000/mission_complete")
        print("🏁 Signal Sent Successfully.")
    except Exception as e:
        print(f"Could not notify dashboard: {e}")

except KeyboardInterrupt:
    print("\n[STOPPED] Mission Aborted")