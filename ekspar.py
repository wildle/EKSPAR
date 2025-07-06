import os
import subprocess
import time
import signal

LOCK_FILE = "camera.lock"
STREAMLIT_CMD = ["streamlit", "run", "frontend/dashboard.py"]
COUNTER_CMD = ["python3", "backend/detection/person_counter.py"]

streamlit_proc = None
counter_proc = None


def is_camera_locked():
    return os.path.exists(LOCK_FILE)

def lock_camera(mode):
    with open(LOCK_FILE, "w") as f:
        f.write(mode)

def unlock_camera():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def start_streamlit():
    global streamlit_proc
    print("[INFO] Starte Dashboard (Streamlit)...")
    streamlit_proc = subprocess.Popen(STREAMLIT_CMD)

def start_counter():
    global counter_proc
    print("[INFO] Starte Personenzählung...")
    counter_proc = subprocess.Popen(COUNTER_CMD)

def stop_counter():
    global counter_proc
    if counter_proc:
        print("[INFO] Beende Personenzählung...")
        counter_proc.terminate()
        counter_proc.wait()
        counter_proc = None

def cleanup():
    print("[INFO] Aufräumen...")
    stop_counter()
    if streamlit_proc:
        print("[INFO] Beende Streamlit...")
        streamlit_proc.terminate()
        streamlit_proc.wait()
    unlock_camera()
    print("[INFO] System beendet.")


def main():
    if is_camera_locked():
        print("[ERROR] Kamera bereits gesperrt. Ein anderer Modus läuft?")
        return

    try:
        lock_camera("counting")
        start_streamlit()
        time.sleep(2)  # optional: warten bis Dashboard geladen ist
        start_counter()

        print("[INFO] EKSPAR-System läuft. STRG+C zum Beenden.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] STRG+C erkannt. Beende...")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
