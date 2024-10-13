from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

# Initialisiere die Kamera nur einmal außerhalb der Schleife
camera = cv2.VideoCapture(0)  # 0 für die Standard-Kamera

# Funktion, um den Video-Feed zu generieren
def generate_frames():
    while True:
        success, frame = camera.read()  # Lies das Bild von der Kamera
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Generiere das Bild im Stream

# Route für die Startseite
@app.route('/')
def index():
    return render_template('index.html')

# Route für den Video-Feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
