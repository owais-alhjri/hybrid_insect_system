import time
from ai.detector import InsectDetector
from mock.mock_drone import MockDrone
from mock.mock_tank import MockTank
from controller.coordinator import Coordinator
from backend.database import DetectionDB
import config

detector = InsectDetector(
    config.MODEL_PATH,
    config.IMG_SIZE,
    config.DRONE_CONF_THRESHOLD
)

db = DetectionDB(config.DB_NAME)

drone = MockDrone(detector)
tank = MockTank(detector)

brain = Coordinator(db) 

print("🚀 Hybrid Insect Detection (Full Spectrum Mode)")
print(f"   Aerial Images: {len(drone.images)}")
print(f"   Ground Images: {len(tank.images)}")
print("-" * 40)

try:
    while True:
        # 1. Drone Scans Top
        drone_detections, location_index = drone.scan()
        
        # CHANGE IS HERE: If finished (-1), we BREAK the loop to stop the program.
        if location_index == -1: 
            print("\n✅ MISSION COMPLETE. All sectors scanned.")
            break

        # 2. Tank Scans Bottom (IMMEDIATELY)
        tank_detections = tank.verify(location_index)

        # 3. Process Both Results
        print(f"\n[SECTOR {location_index + 1} REPORT]")
        
        # Send Drone Data
        if drone_detections:
            brain.process(drone_detections, "AERIAL")
        else:
            print("   Aerial: Clean")

        # Send Tank Data
        if tank_detections:
            brain.process(tank_detections, "GROUND")
        else:
            print("   Ground: Clean")

        print("-" * 40)
        time.sleep(4) 

except KeyboardInterrupt:
    print("\n[STOPPED] Mission Aborted")