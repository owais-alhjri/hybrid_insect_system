class Coordinator:
    def __init__(self, tank, db, verify_threshold):
        self.tank = tank
        self.db = db
        self.verify_threshold = verify_threshold

    def process(self, detections):
        confirmed = []

        for d in detections:
            if d["confidence"] >= self.verify_threshold:
                self.db.insert(d)
                confirmed.append(d)
            else:
                tank_dets = self.tank.verify()
                for td in tank_dets:
                    self.db.insert(td)
                    confirmed.append(td)

        return confirmed
