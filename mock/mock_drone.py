import cv2
import os
import config

class MockDrone:
    def __init__(self, detector):
        self.detector = detector
        self.folder = config.DRONE_IMG_PATH
        
        # Support JPG, JPEG, PNG (Case Insensitive)
        valid_exts = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        
        self.images = sorted([
            f for f in os.listdir(self.folder)
            if f.lower().endswith(valid_exts)
        ])
        self.current_index = 0

    def scan(self):
        # Stop if we have shown all images
        if self.current_index >= len(self.images):
            return None, -1 

        filename = self.images[self.current_index]
        img_path = os.path.join(self.folder, filename)
        
        # Load image
        image = cv2.imread(img_path)

        # SAFETY CHECK: Did the image load?
        if image is None:
            print(f"[ERROR] Could not load image: {filename}. Check file path/integrity.")
            self.current_index += 1
            return [], self.current_index

        # PNG FIX: If image has 4 channels (Transparency), convert to 3 channels
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        print(f"\n[AERIAL SCAN] Processing: {filename}")

        detections = self.detector.detect(image, source="drone")
        
        scanned_index = self.current_index
        self.current_index += 1
        
        return detections, scanned_index