import subprocess
import os

SCRIPT_PATH = os.path.abspath("capture_raw.py")
SYSTEM_PYTHON = "/usr/bin/python3"


def capture_image() -> bool:
    try:
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
