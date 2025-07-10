# backend/camera/capture_raw.py
"""
Einfaches Aufnahmeskript für Einzelbilder mit Picamera2.
Speichert das Bild zur visuellen Konfiguration im Streamlit-Dashboard.
"""

import os
import logging
from picamera2 import Picamera2
from PIL import Image

# ─── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ─── Pfad zum Ausgabebild ───────────────────────────────────────────────────────
OUTPUT_PATH: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "last_config.jpg"))

# ────────────────────────────────────────────────────────────────────────────────
# 📷 Einzelbildaufnahme
# ────────────────────────────────────────────────────────────────────────────────
def main():
    """
    Nimmt ein Einzelbild mit der Raspberry Pi Kamera auf und speichert es im JPEG-Format
    zur späteren Anzeige im Konfigurationsmodus.

    Output:
        static/last_config.jpg
    """
    try:
        # Kamera initialisieren
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration(
            main={"size": (1280, 720)}  # 16:9 für volle Dashboard-Kompatibilität
        ))
        picam2.start()

        # Aufnahme
        frame = picam2.capture_array()
        picam2.close()

        # Speichern
        image = Image.fromarray(frame)
        image.save(OUTPUT_PATH)
        logging.info(f"[OK] Bild gespeichert: {OUTPUT_PATH}")

        # Wichtig für Erfolgserkennung im Subprozess-Aufrufer
        print("[OK]")

    except Exception as e:
        logging.exception("❌ Kameraaufnahme fehlgeschlagen")
    

# ─── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
