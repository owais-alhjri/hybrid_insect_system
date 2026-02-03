import cv2
import os
import random

class MockDrone:
    def __init__(self, detector, image_folder):
        self.detector = detector
        self.images = [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if f.lower().endswith((".jpg", ".png"))
        ]

    def scan(self):
        if not self.images:
            return []

        img_path = random.choice(self.images)
        image = cv2.imread(img_path)

        return self.detector.detect(image, source="drone")
