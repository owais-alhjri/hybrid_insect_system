from ultralytics import YOLO
from datetime import datetime
import uuid
import cv2
import base64

class InsectDetector:
    def __init__(self, model_path, img_size, conf_threshold):
        self.model = YOLO(model_path)
        self.img_size = img_size
        self.conf_threshold = conf_threshold

    def encode_image(self, image):
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    def detect(self, image, source):
        # 1. Run inference (No random effects anymore!)
        results = self.model(
            image,
            imgsz=self.img_size,
            conf=self.conf_threshold,
            iou=0.6,          # This helps remove duplicate boxes for the same bug
            verbose=False
        )[0]

        detections = []
        
        if not results.boxes:
            return []

        # 2. Draw boxes on the image for the dashboard
        annotated_frame = results.plot() 
        img_base64 = self.encode_image(annotated_frame)

        # 3. Process detections
        # We will track which classes we have already seen in this image
        seen_classes = set()

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            conf = float(box.conf[0])

            # CLEANUP RULE: If we already saw this bug class in this image, 
            # and we only want 1 alert per bug type, skip the lower confidence ones.
            if cls_name in seen_classes:
                continue

            seen_classes.add(cls_name)

            detections.append({
                "id": str(uuid.uuid4()),
                "class": cls_name,
                "confidence": round(conf, 3),
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "image": img_base64 
            })

        return detections