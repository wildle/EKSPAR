from flask import Flask, jsonify
import cv2

app = Flask(__name__)

@app.route('/version', methods=['GET'])
def version():
    return jsonify({"opencv_version": cv2.__version__})

if __name__ == "__main__":
    print("Starting OpenCV Flask server on port 5001...")
    app.run(host="0.0.0.0", port=5001)
