
import os
import time
import sys
from datetime import datetime
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp
from backend.detection.hailo_detection import HailoDetection
from hailo_apps_infra.gstreamer_app import app_callback_class
from hailo_apps_infra.hailo_rpi_common import get_default_parser
from gi.repository import Gst 


# 📦 Klassen-Map für dein Modell (ggf. anpassen!)
CLASS_MAP = {
    0: "person",
}

# 🔍 Initialisiere Detection-Adapter
detector = HailoDetection(class_map=CLASS_MAP, target_class="person", conf_thresh=0.4)

# 📸 Callback-Funktion für jedes Inferenz-Frame
#def on_frame(buffer_caps, buffer):
#    detections = detector.extract(buffer_caps, buffer)

#    print(f"\n[{datetime.now().isoformat(timespec='seconds')}] Detections: {len(detections)}")
#    for det in detections:
#        print(f" → class={det.class_id} ({CLASS_MAP[det.class_id]}), conf={det.confidence:.2f}, bbox={det.bbox}")

def on_frame(pad, info, user_data):
    buffer_caps = pad.get_current_caps()
    buffer = info.get_buffer()

    if buffer is None:
        return Gst.PadProbeReturn.OK

    structure = buffer_caps.get_structure(0)
    format_str = structure.get_string("format")
    width = structure.get_value("width")
    height = structure.get_value("height")


    detections = detector.extract(buffer_caps, buffer, width, height)


    print(f"\n[{datetime.now().isoformat(timespec='seconds')}] Detections: {len(detections)}")
    for det in detections:
        print(f" → class={det.class_id} ({CLASS_MAP[det.class_id]}), conf={det.confidence:.2f}, bbox={det.bbox}")

    return Gst.PadProbeReturn.OK

    
# 🔧 Pfad zu deinem YOLOv8m-Modell (.hef)
HEF_PATH = os.path.abspath("model/yolov8m.hef")  # ggf. anpassen

# 🚀 Starte Hailo GStreamer Pipeline
def main():
    print("[INFO] Starte Hailo Object Detection mit YOLOv8m.hef...")

    # Füge den Pfad zum .hef manuell hinzu (falls nicht per CLI gesetzt)
    if "--hef" not in sys.argv:
        sys.argv += ["--hef", "model/yolov8m.hef"]

    parser = get_default_parser()
    user_data = app_callback_class()

    app = GStreamerDetectionApp(
        app_callback=on_frame,
        user_data=user_data,  # falls  keine erweiterte Callbackklasse erforderlich = None
        parser=parser
    )
    app.run()

if __name__ == "__main__":
    main()