# backend/camera/camera_interface.py

import os
import subprocess
import time
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Dynamischer Pfad zur capture_raw.py
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "capture_raw.py"))

# System-Python (außerhalb von .venv), notwendig für libcamera-Kompatibilität
SYSTEM_PYTHON = "/usr/bin/python3"

def capture_image() -> bool:
    """
    Nimmt ein Bild über ein externes Python-Skript auf (capture_raw.py).
    Setzt zuvor das Lockfile auf 'config', um den Konfigurationsmodus zu aktivieren.

    Returns:
        bool: True bei erfolgreicher Aufnahme, False sonst.
    """
    try:
        # Kamera auf Konfigurationsmodus setzen
        with open("camera.lock", "w") as f:
            f.write("config")
        logging.info("Kamera auf 'config' gesetzt.")

        # Kurze Wartezeit für das System (z. B. um Kamera freizugeben)
        time.sleep(1.5)

        # Starte capture_raw.py als Subprozess außerhalb der .venv
        result = subprocess.run(
            [SYSTEM_PYTHON, SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and "[OK]" in result.stdout:
            logging.info("Bild erfolgreich aufgenommen (via Subprozess).")
            return True
        else:
            logging.error("Bildaufnahme fehlgeschlagen:")
            logging.error(result.stdout)
            logging.error(result.stderr)
            return False

    except Exception as e:
        logging.exception("Subprozess konnte nicht ausgeführt werden:")
        return False
