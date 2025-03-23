import os
import cv2
import json
import base64
from flask import Blueprint, jsonify, request

config_api = Blueprint("config_api", __name__)

# Pfade
IMAGE_PATH = "/app/static/last_config.jpg"
CONFIG_PATH = "/app/config/line_config.json"


# 1️⃣ Bild aufnehmen (nur mit picamera2 – klappt nicht im Container!)
@config_api.route("/config/start", methods=["POST"])
def start_config():
    try:
        from picamera2 import Picamera2
    except ImportError:
        return jsonify({"error": "picamera2 not available in Docker container"}), 500

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (1280, 720)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.configure("preview")
    picam2.start()

    frame = picam2.capture_array()
    cv2.imwrite(IMAGE_PATH, frame)

    return jsonify({
        "status": "image_captured",
        "path": IMAGE_PATH
    })


# 2️⃣ Bild + Linie zurückgeben (für das Dashboard)
@config_api.route("/config/image", methods=["GET"])
def get_config_image():
    if not os.path.exists(IMAGE_PATH):
        return jsonify({"error": "No image found"}), 404

    with open(IMAGE_PATH, "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

    line_data = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            line_data = json.load(f)

    return jsonify({
        "image_base64": encoded_image,
        "line": line_data.get("line_y", None),
        "mode": line_data.get("mode", None)
    })


# 3️⃣ Linie manuell setzen
@config_api.route("/config/manual", methods=["POST"])
def manual_line():
    data = request.get_json()

    if not data or "line_y" not in data:
        return jsonify({"error": "Missing line_y"}), 400

    line_y = int(data["line_y"])
    mode = data.get("mode", "horizontal")

    config = {
        "line_y": line_y,
        "mode": mode
    }

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

    return jsonify({
        "status": "line_saved",
        "line_y": line_y,
        "mode": mode
    })
