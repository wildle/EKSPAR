# backend/camera/camera_interface.py
"""
Modul zur externen Kameraauslösung für den Konfigurationsmodus.
Führt `capture_raw.py` außerhalb der virtuellen Umgebung aus, um `libcamera`-Kompatibilität zu gewährleisten.
"""

import os
import subprocess
import time
import logging

# ─── Logging Setup ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ─── Konstanten ─────────────────────────────────────────────────────────────────
SCRIPT_PATH: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "capture_raw.py"))
SYSTEM_PYTHON: str = "/usr/bin/python3"  # Wichtig: außerhalb der .venv

# ────────────────────────────────────────────────────────────────────────────────
# 📷 Bildaufnahme über externes Skript
# ────────────────────────────────────────────────────────────────────────────────
def capture_image() -> bool:
    """
    Führt die Bildaufnahme über ein externes Python-Skript (`capture_raw.py`) aus,
    um ein Kamerabild für den Konfigurationsmodus zu erzeugen.

    Returns:
        bool: True bei Erfolg, False bei Fehler.
    """
    try:
        # Kamera auf Konfigurationsmodus setzen
        with open("camera.lock", "w") as f:
            f.write("config")
        logging.info("📷 Kamera auf 'config' gesetzt.")

        # Kleine Verzögerung (Kamera initialisieren)
        time.sleep(1.5)

        # Subprozess ausführen (außerhalb der .venv)
        result = subprocess.run(
            [SYSTEM_PYTHON, SCRIPT_PATH],
            capture_output=True,
            text=True
        )

        # Erfolg prüfen
        if result.returncode == 0 and "[OK]" in result.stdout:
            logging.info("✅ Bild erfolgreich aufgenommen.")
            return True
        else:
            logging.error("❌ Bildaufnahme fehlgeschlagen.")
            logging.debug(f"stdout:\n{result.stdout}")
            logging.debug(f"stderr:\n{result.stderr}")
            return False

    except Exception as e:
        logging.exception("❌ Ausnahme beim Ausführen von capture_raw.py:")
        return False
