import requests
import time

class Coordinator:
    def __init__(self, db):
        self.db = db
        self.api_url = "http://127.0.0.1:8000/update_live_view"

    def send_ui_update(self, status, detection_data):
        try:
            requests.post(self.api_url, json={
                "status": status,
                "last_detection": detection_data
            })
        except Exception as e:
            print(f"[UI ERROR] {e}")

    def process(self, detections, source_type):
        if not detections:
            return

        # --- STEP 1: SCANNING PHASE (Raw Image) ---
        scan_data = detections[0]
        preview_payload = {
            "image": scan_data['raw_image'], 
            "class": "Scanning...",
            "confidence": 0.0,
            "source": "drone" if source_type == "AERIAL" else "tank"
        }
        
        if source_type == "AERIAL":
            self.send_ui_update("AERIAL_SCANNING", preview_payload)
        else:
            self.send_ui_update("GROUND_SCANNING", preview_payload)
        
        time.sleep(1.5) # Wait for user to see the scan

        # --- STEP 2: RESULT PHASE (Boxed Image) ---
        final_data = detections[0] 
        
        if final_data['found'] == False:
            # Clean/Clear
            status = "AERIAL_CLEAN" if source_type == "AERIAL" else "GROUND_CLEAN"
            print(f"   [CLEAN] {source_type} Sector Clear.")
            self.send_ui_update(status, final_data)
        else:
            # Detected
            status = "AERIAL_DETECTED" if source_type == "AERIAL" else "GROUND_VERIFIED"
            
            # Save to DB & Print
            for d in detections:
                self.db.insert(d)
                print(f"   [DETECTED] {d['class']} | {d['confidence']} | {source_type}")

            # Send UI Update ONCE
            self.send_ui_update(status, final_data)
            
        # REMOVED DUPLICATE CALL HERE