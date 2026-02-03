from ultralytics import YOLO
from datetime import datetime
import uuid

class InsectDetector:
    def __init__(self, model_path, img_size, conf_threshold):
        self.model = YOLO(model_path)
        self.img_size = img_size
        self.conf_threshold = conf_threshold

    def detect(self, image, source):
        results = self.model(
            image,
            imgsz=self.img_size,
            conf=self.conf_threshold,
            verbose=False
        )[0]

        detections = []

        if results.boxes is None:
            return detections

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            conf = float(box.conf[0])

            detections.append({
                "id": str(uuid.uuid4()),
                "class": cls_name,
                "confidence": round(conf, 3),
                "source": source,
                "timestamp": datetime.utcnow().isoformat()
            })

        return detections
