# capture_raw.py
from picamera2 import Picamera2
import time

OUTPUT_PATH = "static/last_config.jpg"

def capture():
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration())
        picam2.start()
        time.sleep(1.5)
        picam2.capture_file(OUTPUT_PATH)
        picam2.close()
        print("[OK] Bild erfolgreich aufgenommen.")
        return True
    except Exception as e:
        print(f"[ERR] Kameraaufnahme fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    capture()
