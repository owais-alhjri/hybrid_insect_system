# ai/detector.py
from ultralytics import YOLO
from datetime import datetime
import uuid
import cv2
import base64
import numpy as np

class InsectDetector:
    def __init__(self, model_path, img_size, conf_threshold):
        self.model = YOLO(model_path)
        self.img_size = img_size
        self.conf_threshold = conf_threshold

    def encode_image(self, image):
        """Convert OpenCV image to Base64 string for the web"""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    def detect(self, image, source):
        # Run inference
        results = self.model(
            image,
            imgsz=self.img_size,
            conf=self.conf_threshold,
            verbose=False
        )[0]

        detections = []
        
        # If nothing detected, return empty list
        if not results.boxes:
            return []

        # Plot the boxes on the image (Draws the visual proof)
        annotated_frame = results.plot() 
        img_base64 = self.encode_image(annotated_frame)

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            conf = float(box.conf[0])

            detections.append({
                "id": str(uuid.uuid4()),
                "class": cls_name,
                "confidence": round(conf, 3),
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "image": img_base64  # <--- WE SEND THE IMAGE NOW
            })

        return detections