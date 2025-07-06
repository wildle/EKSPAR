import cv2
import numpy as np
import time
import json
from hailo_platform import HEF, VDevice
from hailo_model_zoo.core.prepost import PrePostProcessor
from hailo_model_zoo.core.pipeline import PipelineRunner
from hailo_model_zoo.core.factory import model_zoo_factory
from pathlib import Path

# Debug-Modus (True zeigt Fenster mit Ausgaben)
DEBUG_MODE = True

# Konfigurationspfade
BBOX_CONFIG_PATH = "config/bbox_config.json"

# Modelldatei (YOLOv8m)
MODEL_PATH = "resources/yolov8m.hef"

# Zähler
in_count = 0
out_count = 0
current_count = 0

# Dummy-Tracker (ersetzt durch echten Tracker im nächsten Schritt)
class DummyTracker:
    def __init__(self):
        self.counter = 0

    def update(self, detections):
        tracked = []
        for det in detections:
            self.counter += 1
            tracked.append({"id": self.counter, "bbox": det})
        return tracked

def load_bbox_config(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Konnte Bounding Box nicht laden: {e}")
        return None

def draw_debug(frame, tracks, bbox_area):
    for obj in tracks:
        x1, y1, x2, y2 = obj["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f'ID {obj["id"]}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
    if bbox_area:
        x1, y1, x2, y2 = bbox_area
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        cv2.putText(frame, "Zählbereich", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)
    cv2.imshow("EKSPAR Live Debug", frame)
    cv2.waitKey(1)

def run_counter():
    print("[INFO] Starte Personenzählung...")
    
    # Kamera-Setup (OpenCV - später Hailo-Kamera)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Kamera nicht verfügbar")
        return

    # Tracker initialisieren
    tracker = DummyTracker()

    # BBox-Konfiguration laden
    bbox_area = load_bbox_config(BBOX_CONFIG_PATH)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Kein Kamerabild erhalten")
            break

        height, width = frame.shape[:2]

        # (Platzhalter) Inferenz – Bounding Boxes simulieren
        # TODO: Hailo YOLO Inferenz einbauen
        dummy_detections = [
            [int(0.3*width), int(0.3*height), int(0.5*width), int(0.6*height)],
            [int(0.6*width), int(0.4*height), int(0.8*width), int(0.7*height)]
        ]

        tracks = tracker.update(dummy_detections)

        # TODO: Richtungsanalyse einbauen

        if DEBUG_MODE:
            draw_debug(frame.copy(), tracks, bbox_area)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_counter()
