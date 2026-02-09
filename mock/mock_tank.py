import cv2
import os
import config

class MockTank:
    def __init__(self, detector):
        self.detector = detector
        self.folder = config.TANK_IMG_PATH
        valid_exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        
        if os.path.exists(self.folder):
            self.images = sorted([f for f in os.listdir(self.folder) if f.lower().endswith(valid_exts)])
        else:
            self.images = []

    def verify(self, target_index):
        if not self.images or target_index < 0 or target_index >= len(self.images):
            return []

        image = cv2.imread(os.path.join(self.folder, self.images[target_index]))
        if image is None: return []
        if image.shape[2] == 4: image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # Run detection
        detections = self.detector.detect(image, source="tank")

        return detections