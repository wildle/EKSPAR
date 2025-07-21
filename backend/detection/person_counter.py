# person_counter.py – Zähllogik für das EKSPAR-System
"""
Startet die Live-Personenzählung mit Kamera und YOLOv11n.
Verwendet den definierten Zählbereich (Bounding Box) und eine Eintrittsrichtung.
"""

# ─── Imports ───────────────────────────────────────────────────────────────────
import os
import time
import json
import datetime
import sqlite3
import logging
from picamera2 import Picamera2
from ultralytics.solutions import ObjectCounter
import cv2  # Nur für Debug-Visualisierung

# ─── Logging Setup (ultralytics Warnungen unterdrücken) ────────────────────────
logging.getLogger("ultralytics").setLevel(logging.ERROR)
logging.getLogger("yolo").setLevel(logging.ERROR)

# Ultralytics Console-Output komplett deaktivieren
os.environ["YOLO_VERBOSE"] = "False"
os.environ["ULTRALYTICS_VERBOSE"] = "False"

# ─── Konfiguration ─────────────────────────────────────────────────────────────
# MODEL_PATH = "models/yolo11n.pt"          # PyTorch (3.1 FPS, 310ms)
MODEL_PATH = "models/yolo11n_ncnn_model"    # NCNN (6.7 FPS, 150ms) ✅
BBOX_CONFIG_PATH = "backend/config/bbox_config.json"
DIRECTION_CONFIG_PATH = "backend/config/direction_config.json"
EXPORT_PATH = "data/counter.json"
LOG_DB_PATH = "data/log.db"
LOCK_PATH = "camera.lock"

HEADLESS_MODE = False  # False = Debug-Modus mit OpenCV-Fenster
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ─── Kamera-Modus prüfen ───────────────────────────────────────────────────────
def is_counting_mode() -> bool:
    """Prüft, ob der Zählmodus aktiv ist.

    Gibt True zurück, wenn die Lock-Datei 'camera.lock' den Modus 'counting' enthält.
    
    Returns:
        bool: True wenn Zählmodus aktiv, sonst False.
    """
    if not os.path.exists(LOCK_PATH):
        return False
    with open(LOCK_PATH, "r") as f:
        return f.read().strip() == "counting"

# ─── Bounding Box laden ────────────────────────────────────────────────────────
def load_bbox() -> dict | None:
    """Lädt die Bounding-Box-Konfiguration aus der JSON-Datei.

    Returns:
        dict | None: Bounding-Box-Daten (x, y, w, h) oder None bei Fehler.
    """
    if not os.path.exists(BBOX_CONFIG_PATH):
        print("[WARN] Keine Zählbereich-Konfiguration gefunden.")
        return None
    try:
        with open(BBOX_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der bbox_config.json: {e}")
        return None

# ─── Richtungskonfiguration laden ──────────────────────────────────────────────
def load_direction_config() -> dict | None:
    """Lädt die Eintrittsrichtung aus der JSON-Datei.

    Returns:
        dict | None: Richtungskonfiguration mit 'angle'-Wert oder None bei Fehler.
    """
    if not os.path.exists(DIRECTION_CONFIG_PATH):
        print("[WARN] Keine Richtungskonfiguration gefunden.")
        return None
    try:
        with open(DIRECTION_CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Fehler beim Laden der direction_config.json: {e}")
        return None

# ─── Zähldaten in SQLite schreiben ─────────────────────────────────────────────
def log_to_db(data: dict) -> None:
    """Schreibt Zähldaten in die lokale SQLite-Datenbank.

    Erstellt die Tabelle 'log' bei Bedarf und speichert einen neuen Eintrag.

    Args:
        data (dict): Zähldaten im Format mit Schlüsseln
            'timestamp', 'in', 'out', 'current', 'total_tracks'.
    """
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
        print(f"[ERROR] Fehler beim Schreiben in die Datenbank: {e}")

# ─── Zähldaten exportieren (JSON + DB) ─────────────────────────────────────────
def export_counts(results) -> None:
    """Exportiert Zähldaten aus einem Detection-Ergebnis.

    Erstellt ein JSON-Dokument mit Zeitstempel und Zählwerten und speichert zusätzlich in SQLite.

    Args:
        results: Ergebnisobjekt von ObjectCounter mit Attributen
            'in_count', 'out_count', 'total_tracks'.
    """
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
        print(f"[ERROR] Fehler beim Exportieren der Zähldaten: {e}")

# ─── Hauptfunktion ─────────────────────────────────────────────────────────────
def main() -> None:
    """Startet die Live-Personenzählung mit Kamera und ObjectCounter.

    Ablauf:
    - Lädt Bounding Box und Richtungskonfiguration
    - Initialisiert Kamera und ObjectCounter
    - Führt kontinuierliche Erkennung durch
    - Exportiert Zähldaten als JSON + SQLite
    - Unterstützt Debug-Modus mit OpenCV-Vorschau (optional)
    """
    print("[INFO] Starte Personenzählung mit direkter Kamera...")

    # ── Konfiguration laden ──
    bbox = load_bbox()
    if not bbox:
        print("[ERROR] Kein Zählbereich definiert.")
        return

    direction = load_direction_config()
    if not direction or "angle" not in direction:
        print("[ERROR] Keine gültige Richtungskonfiguration gefunden.")
        return

    entry_angle = direction["angle"]
    opposite_angle = (entry_angle + 180) % 360
    print(f"[INFO] Eintrittsrichtung: {entry_angle}° → Gegenrichtung: {opposite_angle}°")

    # ── Region definieren ──
    region = [
        (bbox["x"], bbox["y"]),
        (bbox["x"] + bbox["w"], bbox["y"]),
        (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"]),
        (bbox["x"], bbox["y"] + bbox["h"])
    ]

    # ── ObjectCounter initialisieren ──
    counter = ObjectCounter(
        model=MODEL_PATH,
        classes=[0],  # Klasse 0 = Personen
        region=region,
        show=False,
        up_angle=entry_angle,
        down_angle=opposite_angle
    )

    # ── Kamera konfigurieren ──
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (FRAME_WIDTH, FRAME_HEIGHT)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()

    # ── Performance-Tracking (auskommentiert nach Benchmark) ──
    # frame_count = 0
    # start_time = time.time()
    # inference_times = []

    try:
        while True:
            # Prüfen, ob der Modus gewechselt wurde
            if not is_counting_mode():
                print("[INFO] Konfigurationsmodus erkannt – Zählung wird gestoppt.")
                break

            # Frame aufnehmen und verarbeiten
            frame = picam2.capture_array()
            
            # Performance-Messung (auskommentiert nach Benchmark)
            # inference_start = time.time()
            results = counter.process(frame)
            # inference_end = time.time()
            
            # Statistiken sammeln (auskommentiert nach Benchmark)
            # frame_count += 1
            # inference_time = inference_end - inference_start
            # inference_times.append(inference_time)
            
            # Alle 30 Frames: Performance ausgeben (auskommentiert nach Benchmark)
            # if frame_count % 30 == 0:
            #     elapsed = time.time() - start_time
            #     fps = frame_count / elapsed
            #     avg_inference = sum(inference_times[-30:]) / min(30, len(inference_times))
            #     print(f"[PERF] FPS: {fps:.1f} | Avg Inference: {avg_inference*1000:.0f}ms | Model: {MODEL_PATH}")
            #     
            #     # Memory-sparend: nur letzte 100 Zeiten behalten
            #     if len(inference_times) > 100:
            #         inference_times = inference_times[-100:]

            # Spezialfall: Richtung 180° → Zählung umkehren
            if entry_angle == 180:
                results.in_count, results.out_count = results.out_count, results.in_count

            # Zähldaten exportieren
            export_counts(results)

            # Debug-Vorschau (optional)
            if not HEADLESS_MODE:
                frame_to_show = results.plot_im
                if "window_initialized" not in globals():
                    cv2.namedWindow("Zählung", cv2.WINDOW_NORMAL)
                    globals()["window_initialized"] = True

                cv2.imshow("Zählung", frame_to_show)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\n[INFO] Abbruch durch Benutzer.")

    except Exception as e:
        print(f"[ERROR] Unerwarteter Fehler: {e}")

    finally:
        picam2.stop()
        if not HEADLESS_MODE:
            cv2.destroyAllWindows()
        print("[INFO] Personenzählung gestoppt.")

# ─── Startpunkt ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Einstiegspunkt für das EKSPAR-Zählsystem
    main()
