# backend/camera/capture_raw.py

import os
import logging
from picamera2 import Picamera2
from PIL import Image

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Pfad zur Bildausgabe
OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "last_config.jpg"))

def main():
    """
    Nimmt ein Einzelbild mit Picamera2 auf und speichert es als JPEG.
    Das Bild dient als Grundlage für die visuelle Konfiguration im Dashboard.
    """
    try:
        # Kamera initialisieren
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration(
            main={"size": (1280, 720)}  # 16:9 Format
        ))
        picam2.start()

        # Bild aufnehmen
        frame = picam2.capture_array()
        picam2.close()

        # In PIL-Image umwandeln und speichern
        image = Image.fromarray(frame)
        image.save(OUTPUT_PATH)
        logging.info(f"[OK] Bild gespeichert: {OUTPUT_PATH}")

    except Exception as e:
        logging.exception("Kameraaufnahme fehlgeschlagen")

if __name__ == "__main__":
    main()
