import requests

class Coordinator:
    def __init__(self, db):
        self.db = db
        self.api_url = "http://127.0.0.1:8000/update_live_view"

    def send_ui_update(self, status, detection=None):
        try:
            requests.post(self.api_url, json={
                "status": status,
                "last_detection": detection
            })
        except:
            pass 

    def process(self, detections, source_type):
        """
        Simply logs and displays whatever is sent to it.
        source_type: 'AERIAL' or 'GROUND'
        """
        for d in detections:
            # 1. Save to Database
            self.db.insert(d)
            
            # 2. Send to Dashboard
            if source_type == "AERIAL":
                self.send_ui_update("AERIAL_DETECTED", d)
                print(f"   [DETECTED] {d['class']} | {d['confidence']} | DRONE (Canopy)")
            
            elif source_type == "GROUND":
                self.send_ui_update("GROUND_VERIFIED", d) # We keep the UI status name for compatibility
                print(f"   [DETECTED] {d['class']} | {d['confidence']} | TANK (Trunk/Soil)")