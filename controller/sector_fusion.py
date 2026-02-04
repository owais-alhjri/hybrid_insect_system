# controller/sector_fusion.py

from datetime import datetime

class SectorFusion:
    def __init__(self):
        self.buffer = {}

    def add_result(self, sector_id, source, detections):
        if sector_id not in self.buffer:
            self.buffer[sector_id] = {
                "AERIAL": None,
                "GROUND": None,
                "timestamp": datetime.utcnow().isoformat()
            }

        self.buffer[sector_id][source] = detections

    def is_ready(self, sector_id):
        s = self.buffer.get(sector_id)
        return s and s["AERIAL"] is not None and s["GROUND"] is not None

    def fuse(self, sector_id):
        s = self.buffer.pop(sector_id)

        aerial = s["AERIAL"]
        ground = s["GROUND"]

        fused = {
            "sector": sector_id,
            "timestamp": s["timestamp"],
            "canopy_threats": aerial,
            "ground_threats": ground,
            "status": self._classify(aerial, ground)
        }

        return fused

    def _classify(self, aerial, ground):
        if aerial and ground:
            return "MULTI_LAYER_INFESTATION"
        if aerial:
            return "CANOPY_INFESTATION"
        if ground:
            return "GROUND_INFESTATION"
        return "SECTOR_HEALTHY"
