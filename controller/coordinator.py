import requests

class Coordinator:
    def __init__(self, tank, db, verify_threshold):
        self.tank = tank
        self.db = db
        self.verify_threshold = verify_threshold
        self.api_url = "http://127.0.0.1:8000/update_live_view"

    def send_ui_update(self, status, detection=None):
        try:
            requests.post(self.api_url, json={
                "status": status,
                "last_detection": detection
            })
        except:
            pass # Ignore API errors during demo if server isn't up

    def process(self, detections):
        confirmed = []

        for d in detections:
            # 1. Drone detects something
            self.send_ui_update("AERIAL_DETECTED", d)
            
            if d["confidence"] >= self.verify_threshold:
                # High confidence: Confirm immediately
                self.db.insert(d)
                confirmed.append(d)
            else:
                # Low confidence: Trigger Tank
                self.send_ui_update("DEPLOYING_GROUND_UNIT", d)
                
                # Simulate tank travel time
                import time; time.sleep(1.5) 

                tank_dets = self.tank.verify()
                
                for td in tank_dets:
                    self.send_ui_update("GROUND_VERIFIED", td)
                    self.db.insert(td)
                    confirmed.append(td)

        return confirmed