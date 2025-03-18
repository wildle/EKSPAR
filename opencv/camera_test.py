import cv

def main():
    """ Kamerastream mit OpenCV anzeigen """
    cap = cv2.VideoCapture("libcamerasrc ! videoconvert ! appsink", cv2.CAP_GSTREAMER)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Fehler: Kein Bild erhalten")
            break
        
        cv2.imshow("Live Kamera - Open CV + libcamera", frame)

        # Beenden mit 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()        
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()