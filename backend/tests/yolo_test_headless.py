from picamera2 import Picamera2
from ultralytics import YOLO
import time

# Modellpfad
model_path = "/home/jarvis/EKSPAR/model/yolo11n.pt"
model = YOLO(model_path)

# Kamera konfigurieren
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()

print("YOLOv11n Headless-Erkennung (nur 'person') gestartet. Mit STRG+C beenden.\n")

CONFIDENCE_THRESHOLD = 0.5  # Mindest-Konfidenz für Anzeige

while True:
    frame = picam2.capture_array()
    results = model(frame, verbose=False)

    boxes = results[0].boxes
    person_count = 0

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Nur Personen anzeigen (Klasse 0 == 'person' bei COCO)
            if model.names[cls] == 'person' and conf >= CONFIDENCE_THRESHOLD:
                person_count += 1

    if person_count > 0:
        print(f"→ Personen erkannt: {person_count}")

    time.sleep(0.1)
