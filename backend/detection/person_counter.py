import os
import time
import json
import datetime
import sqlite3
from picamera2 import Picamera2
from ultralytics.solutions import ObjectCounter
import cv2  # Nur für Debug-Visualisierung

# ─── Konfiguration ───
MODEL_PATH = "models/yolo11n.pt"
BBOX_CONFIG_PATH = "backend/config/bbox_config.json"
EXPORT_PATH = "data/counter.json"
LOG_DB_PATH = "data/log.db"
LOCK_PATH = "camera.lock"
HEADLESS_MODE = True  # False = Debug mit OpenCV Fenster | True = HEADLESS Modus ohne GUI
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ─── Kamera sperre prüfen ───
def is_counting_mode():
    if not os.path.exists(LOCK_PATH):
        return False
    with open(LOCK_PATH, "r") as f:
        return f.read().strip() == "counting"

# ─── Bounding Box laden ───
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

# ─── Zähldaten speichern ───
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

# ─── Hauptfunktion ───
def main():
    print("[INFO] Starte Personenzählung mit direkter Kamera...")

    bbox = load_bbox()
    if not bbox:
        print("[ERROR] Kein Zählbereich definiert.")
        return

    region = [
        (bbox["x"], bbox["y"]),
        (bbox["x"] + bbox["w"], bbox["y"]),
        (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"]),
        (bbox["x"], bbox["y"] + bbox["h"])
    ]

    counter = ObjectCounter(
        model=MODEL_PATH,
        classes=[0],
        region=region,
        show=False
    )

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (FRAME_WIDTH, FRAME_HEIGHT)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()

    try:
        while True:
            if not is_counting_mode():
                print("[INFO] Konfigurationsmodus erkannt – Zählung wird beendet.")
                picam2.stop()
                if not HEADLESS_MODE:
                    cv2.destroyAllWindows()
                os._exit(0)


            frame = picam2.capture_array()
            results = counter.process(frame)
            #print(f"[DEBUG] results.plot_im = {hasattr(results, 'plot_im')}")
            export_counts(results)

            if not HEADLESS_MODE:
                frame_to_show = results.plot_im

                if "window_initialized" not in globals():
                    cv2.namedWindow("Zählung", cv2.WINDOW_NORMAL)
                    globals()["window_initialized"] = True

                cv2.imshow("Zählung", frame_to_show)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break


    except KeyboardInterrupt:
        print("\n[INFO] Abbruch durch Benutzer.")

    except Exception as e:
        print(f"[ERROR] Fehler: {e}")

    finally:
        picam2.stop()
        if not HEADLESS_MODE:
            cv2.destroyAllWindows()
        print("[INFO] Personenzählung gestoppt.")


if __name__ == "__main__":
    main()
