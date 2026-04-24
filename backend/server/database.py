import sqlite3

class DetectionDB:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id TEXT PRIMARY KEY,
            insect TEXT,
            confidence REAL,
            source TEXT,
            timestamp TEXT
        )
        """)
        self.conn.commit()

    def insert(self, d):
        self.conn.execute("""
        INSERT OR IGNORE INTO detections
        (id, insect, confidence, source, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """, (
            d["id"],
            d["class"],
            d["confidence"],
            d["source"],
            d["timestamp"]
        ))
        self.conn.commit()
