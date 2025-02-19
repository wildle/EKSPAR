from flask import Flask, jsonify
from ultralytics import YOLO

app = Flask(__name__)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"yolo": "YOLO API is running!"})

@app.route('/yolo_version', methods=['GET'])
def yolo_version():
    return jsonify({"ultralytics_version": YOLO.__version__})

if __name__ == "__main__":
    print("Starting YOLO Flask server on port 5002...")
    app.run(host="0.0.0.0", port=5002)
