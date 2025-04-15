from picamera2 import Picamera2
from PIL import Image
import os

OUTPUT_PATH = os.path.join("static", "last_config.jpg")

def main():
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_still_configuration(
            main={"size": (1280, 720)}
        ))
        picam2.start()
        frame = picam2.capture_array()
        picam2.close()

        # Bild speichern
        image = Image.fromarray(frame)
        image.save(OUTPUT_PATH)
        print("[OK] Bild gespeichert:", OUTPUT_PATH)

    except Exception as e:
        print("[ERR] Kameraaufnahme fehlgeschlagen:", e)

if __name__ == "__main__":
    main()
