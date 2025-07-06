# backend/detection/hailo_detection.py

from hailo_apps_infra.hailo_rpi_common import get_numpy_from_buffer

class Detection:
    def __init__(self, class_id, confidence, bbox):
        self.class_id = class_id
        self.confidence = confidence
        self.bbox = bbox  # Format: [x1, y1, x2, y2]

class HailoDetection:
    def __init__(self, class_map: dict, target_class: str = "person", conf_thresh: float = 0.4):
        self.class_map = class_map
        self.target_class = target_class
        self.conf_thresh = conf_thresh

    # def extract(self, buffer_caps, buffer) -> list:
    def extract(self, buffer_caps, buffer, width, height):
        """
        Extrahiert alle Detektionen (Bounding Boxes) aus dem Inferenzbuffer
        """
        # frame_data = get_numpy_from_buffer(buffer, buffer_caps)
        structure = buffer_caps.get_structure(0)
        format_str = structure.get_string("format")
        frame_data = get_numpy_from_buffer(buffer, format_str, width, height)



        detections = []
        for row in frame_data:
            try:
                class_id = int(row[0])
                conf = float(row[1])
                x1, y1, x2, y2 = map(int, row[2:6])
            except Exception as e:
                print(f"[WARN] Fehler beim Parsen der Detektion: {e}")
                continue

            if self.class_map.get(class_id) == self.target_class and conf >= self.conf_thresh:
                detections.append(Detection(class_id, conf, [x1, y1, x2, y2]))

        return detections