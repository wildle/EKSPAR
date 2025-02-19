import requests
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask is running!"

@app.route('/test_opencv', methods=['GET'])
def test_opencv():
    try:
        # Korrekte OpenCV-Adresse mit Port 5001
        response = requests.get("http://docker_opencv_1:5001/version")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test_yolo', methods=['GET'])
def test_yolo():
    try:
        # YOLO ansprechen
        response = requests.get("http://docker_yolo_1:5002/status")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
