# backend/camera/camera_interface.py

import os
import subprocess
import time

# Pfad zur capture_raw.py dynamisch bestimmen
SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "capture_raw.py"))

# Pfad zu Systempython
SYSTEM_PYTHON = "/usr/bin/python3"

def capture_image() -> bool:

        # Kamera auf Konfigurationsmodus setzen
    with open("camera.lock", "w") as f:
        f.write("config")
    print("[INFO] Kamera auf 'config' gesetzt.")

    # Warten, bis person_counter.py Kamera freigegeben hat
    time.sleep(1.5)

    try:
        # Starte capture_raw.py als Subprozess
        result = subprocess.run(
            [SYSTEM_PYTHON, SCRIPT_PATH],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and "[OK]" in result.stdout:
            print("[INFO] Bild erfolgreich aufgenommen (via Subprozess).")

            return True
        else:
            print("[ERROR] Aufnahme fehlgeschlagen:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[EXCEPTION] Subprozess konnte nicht ausgeführt werden: {e}")
        return False
