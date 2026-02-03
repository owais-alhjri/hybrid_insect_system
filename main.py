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

drone = MockDrone(detector, config.DEMO_IMAGE_FOLDER)
tank = MockTank(detector, config.DEMO_IMAGE_FOLDER)

brain = Coordinator(tank, db, config.VERIFY_THRESHOLD)

print("🚀 Hybrid Insect Detection Demo (REAL MODEL)")

while True:
    detections = drone.scan()
    if detections:
        confirmed = brain.process(detections)
        for d in confirmed:
            print(f"[DETECTED] {d['class']} | {d['confidence']} | {d['source']}")
    time.sleep(2)
