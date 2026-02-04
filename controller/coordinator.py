import requests
import time

class Coordinator:
    def __init__(self, db):
        self.db = db
        # Ensure this URL matches your run_demo.py output
        self.api_url = "http://127.0.0.1:8000/update_live_view"

    def send_ui_update(self, status, detection):
        try:
            requests.post(self.api_url, json={
                "status": status,
                "last_detection": detection
            })
        except Exception as e:
            print(f"[UI ERROR] Could not update dashboard: {e}")

    def process(self, detections, source_type):
        # Safety check (should not happen with new detector, but good practice)
        if not detections:
            return

        # --- STEP 1: SCANNING PHASE (Always show this first) ---
        # We grab the first item to get the raw image
        scan_data = detections[0]
        
        preview_payload = {
            "image": scan_data['raw_image'], # Always show clean image first
            "class": "Scanning...",
            "confidence": 0.0
        }
        
        if source_type == "AERIAL":
            self.send_ui_update("AERIAL_SCANNING", preview_payload)
        else:
            self.send_ui_update("GROUND_SCANNING", preview_payload)
        
        # Wait 2 seconds so the user sees the "Scanning" animation
        time.sleep(2.0)

        # --- STEP 2: RESULT PHASE ---
        # Check if the FIRST item says we found something
        if detections[0]['found'] == False:
            # CASE: NO BUGS
            if source_type == "AERIAL":
                self.send_ui_update("AERIAL_CLEAN", scan_data)
                print(f"   [CLEAN] Aerial Sector Clear.")
            else:
                self.send_ui_update("GROUND_CLEAN", scan_data)
                print(f"   [CLEAN] Ground Sector Clear.")
        
        else:
            # CASE: BUGS FOUND
            # Update UI with the BOXED image from the first detection
            final_data = detections[0]
            if source_type == "AERIAL":
                self.send_ui_update("AERIAL_DETECTED", final_data)
            else:
                self.send_ui_update("GROUND_VERIFIED", final_data)

        # --- STEP 3: SHOW DETECTED RESULT & SAVE ---
        # Save to DB & log to terminal; only do inserts here to avoid duplicates
        for d in detections:
            # Save to Database
            self.db.insert(d) 

            # Log to Terminal
            if source_type == "AERIAL":
                print(f"   [DETECTED] {d['class']} | {d['confidence']} | DRONE")
            else:
                print(f"   [DETECTED] {d['class']} | {d['confidence']} | TANK")

        # Update UI (Use the first detection, which contains the image with ALL boxes)
        final_detection_data = detections[0]
        
        if source_type == "AERIAL":
            self.send_ui_update("AERIAL_DETECTED", final_detection_data)
        else:
            self.send_ui_update("GROUND_VERIFIED", final_detection_data)