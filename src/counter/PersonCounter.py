import os
import time
import json
import datetime
import numpy as np
from ultralytics.solutions import ObjectCounter

# ──────────────────────────────────────────────
# Konfiguration
MODEL_PATH = "model/yolo11n.pt"
LIVE_FRAME_PATH = "data/live/live_frame.npy"
BBOX_CONFIG_PATH = "backend/config/bbox_config.json"
EXPORT_PATH = "data/counter.json"
CONFIDENCE_THRESHOLD = 0.25
# ──────────────────────────────────────────────

def load_bbox():
    if not os.path.exists(BBOX_CONFIG_PATH):
        print("[WARN] Keine Zählbereich-Konfiguration gefunden.")
        return None
    try:
        with open(BBOX_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der bbox_config.json: {e}")
        return None

def export_counts(results):
    try:
        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "in": getattr(results, "in_count", 0),
            "out": getattr(results, "out_count", 0),
            "current": getattr(results, "in_count", 0) - getattr(results, "out_count", 0),
            "total_tracks": getattr(results, "total_tracks", 0)
        }

        with open(EXPORT_PATH, "w") as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        print(f"[WARN] Fehler beim Exportieren der Zähldaten: {e}")

def main():
    print("[INFO] Starte headless Personenzählung...")
    bbox = load_bbox()
    if not bbox:
        print("[ERROR] Kein Zählbereich definiert.")
        return

    # Skalierung von 720px Canvas auf 1280px Frame
    canvas_width = 720
    original_width = 1280
    scale = original_width / canvas_width

    scaled_bbox = {
        "x": int(bbox["x"] * scale),
        "y": int(bbox["y"] * scale),
        "w": int(bbox["w"] * scale),
        "h": int(bbox["h"] * scale)
    }

    region = [
        (scaled_bbox["x"], scaled_bbox["y"]),
        (scaled_bbox["x"] + scaled_bbox["w"], scaled_bbox["y"]),
        (scaled_bbox["x"] + scaled_bbox["w"], scaled_bbox["y"] + scaled_bbox["h"]),
        (scaled_bbox["x"], scaled_bbox["y"] + scaled_bbox["h"])
    ]

    counter = ObjectCounter(
        model=MODEL_PATH,
        classes=[0],  # nur Personen zählen
        region=region,
        stream=False,
        show=False  # HEADLESS!
    )

    while True:
        try:
            if not os.path.exists(LIVE_FRAME_PATH):
                time.sleep(0.2)
                continue

            frame = None
            for _ in range(3):
                try:
                    frame = np.load(LIVE_FRAME_PATH, allow_pickle=False)
                    if frame is not None and frame.shape[0] > 0:
                        break
                except Exception:
                    time.sleep(0.05)

            if frame is None:
                print("[WARN] Frame konnte nicht gelesen werden.")
                continue

            results = counter(frame)
            export_counts(results)

        except KeyboardInterrupt:
            print("\n[INFO] Abbruch durch Benutzer.")
            break

        except Exception as e:
            print(f"[ERROR] Fehler: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
