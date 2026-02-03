import cv2
import os
import config

class MockTank:
    def __init__(self, detector):
        self.detector = detector
        self.folder = config.TANK_IMG_PATH
        
        valid_exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        
        self.images = sorted([
            f for f in os.listdir(self.folder)
            if f.lower().endswith(valid_exts)
        ])

    def verify(self, target_index):
        # Safety: Check if index exists
        if target_index < 0 or target_index >= len(self.images):
            print(f"[GROUND UNIT] Error: No matching ground view for index {target_index}")
            return []

        filename = self.images[target_index]
        img_path = os.path.join(self.folder, filename)
        
        image = cv2.imread(img_path)

        # SAFETY CHECK
        if image is None:
            print(f"[ERROR] Could not load ground image: {filename}")
            return []

        # PNG FIX
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
        print(f"[GROUND UNIT] Verifying Location: {filename}")

        return self.detector.detect(image, source="tank")