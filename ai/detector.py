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
        # 1. ENCODE RAW IMAGE (Always needed for scanning view)
        raw_img_base64 = self.encode_image(image)

        # 2. Run Inference
        results = self.model(
            image,
            imgsz=self.img_size,
            conf=self.conf_threshold,
            iou=0.6,
            verbose=False
        )[0]

        detections = []

        # --- SCENARIO A: NO BUGS FOUND ---
        if not results.boxes:
            # Return a "Clean" entry so the dashboard still updates
            return [{
                "id": str(uuid.uuid4()),
                "class": "None",
                "confidence": 0.0,
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "image": raw_img_base64,      # Show clean image
                "raw_image": raw_img_base64,  # Show clean image
                "found": False                # FLAG: Nothing found
            }]

        # --- SCENARIO B: BUGS FOUND ---
        # Create Boxed Image
        annotated_frame = results.plot() 
        boxed_img_base64 = self.encode_image(annotated_frame)

        seen_classes = set()

        for box in results.boxes:
            cls_id = int(box.cls[0])
            cls_name = self.model.names[cls_id]
            conf = float(box.conf[0])

            if cls_name in seen_classes:
                continue
            seen_classes.add(cls_name)

            detections.append({
                "id": str(uuid.uuid4()),
                "class": cls_name,
                "confidence": round(conf, 3),
                "source": source,
                "timestamp": datetime.utcnow().isoformat(),
                "image": boxed_img_base64,   # Show boxed image
                "raw_image": raw_img_base64, # Show clean image
                "found": True                # FLAG: Bug found
            })

        return detections