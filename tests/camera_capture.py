# camera_capture.py
import time
import numpy as np
from picamera2 import Picamera2

SAVE_PATH = "live_frame.npy"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

def main():
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (FRAME_WIDTH, FRAME_HEIGHT)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()

    print("[INFO] Kameraaufnahme gestartet...")
    try:
        while True:
            frame = picam2.capture_array()
            np.save(SAVE_PATH, frame)
            time.sleep(0.1)  # 10 FPS (anpassbar)
    except KeyboardInterrupt:
        print("[INFO] Aufnahme gestoppt.")

if __name__ == "__main__":
    main()
