import os
import time
import json
import datetime
import numpy as np
import sqlite3
from ultralytics.solutions import ObjectCounter

# ──────────────────────────────────────────────
# Konfiguration
MODEL_PATH = "models/yolo11n.pt"
LIVE_FRAME_PATH = "data/live/live_frame.npy"
BBOX_CONFIG_PATH = "backend/config/bbox_config.json"
EXPORT_PATH = "data/counter.json"
LOG_DB_PATH = "data/log.db"
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

def log_to_db(data):
    try:
        conn = sqlite3.connect(LOG_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS log (
                timestamp TEXT,
                in_count INTEGER,
                out_count INTEGER,
                current_count INTEGER,
                total_tracks INTEGER
            )
        """)
        cursor.execute("""
            INSERT INTO log (timestamp, in_count, out_count, current_count, total_tracks)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data["timestamp"],
            data["in"],
            data["out"],
            data["current"],
            data["total_tracks"]
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] Fehler beim Schreiben in die Datenbank: {e}")

def export_counts(results):
    try:
        in_count = getattr(results, "in_count", 0)
        out_count = getattr(results, "out_count", 0)
        current = max(0, in_count - out_count)

        data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "in": in_count,
            "out": out_count,
            "current": current,
            "total_tracks": getattr(results, "total_tracks", 0)
        }

        with open(EXPORT_PATH, "w") as f:
            json.dump(data, f, indent=2)

        log_to_db(data)

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

    # Verwende die gespeicherten Werte direkt – sie sind bereits auf 1280×720 angepasst
    scaled_bbox = bbox


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
        show=False
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
