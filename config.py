# config.py

MODEL_PATH = "ai/model/oman_insect_best_v7.pt"
IMG_SIZE = 640

# Raise this to 0.70 (70%)
# Only show me the bug if the AI is SURE it's a bug.
DRONE_CONF_THRESHOLD = 0.50 

DRONE_IMG_PATH = "mock/aerial_view"
TANK_IMG_PATH = "mock/ground_view"

DB_NAME = "detections.db"