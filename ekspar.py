import os
import subprocess
import time

LOCK_FILE = "camera.lock"
STREAMLIT_CMD = ["streamlit", "run", "frontend/dashboard.py"]
COUNTER_CMD = ["python3", "backend/detection/person_counter.py"]

streamlit_proc = None
counter_proc = None


def get_camera_mode():
    if not os.path.exists(LOCK_FILE):
        return None
    with open(LOCK_FILE, "r") as f:
        return f.read().strip()


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
    if counter_proc is None or counter_proc.poll() is not None:
        print("[INFO] Starte Personenzählung...")
        counter_proc = subprocess.Popen(COUNTER_CMD)


def stop_counter():
    global counter_proc
    if counter_proc and counter_proc.poll() is None:
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


def config_exists():
    return os.path.exists("backend/config/bbox_config.json")


def main():
    if get_camera_mode() == "config":
        print("[ERROR] Kamera bereits im Konfigurationsmodus. Ein anderer Prozess läuft?")
        return

    if not config_exists():
        print("[ERROR] Keine bbox_config.json gefunden. Bitte zuerst Konfiguration durchführen.")
        return

    try:
        lock_camera("counting")
        start_streamlit()
        time.sleep(2)  # Dashboard initialisieren lassen
        start_counter()

        print("[INFO] EKSPAR-System läuft. STRG+C zum Beenden.")
        last_mode = get_camera_mode()

        while True:
            time.sleep(1)
            current_mode = get_camera_mode()

            # Konfigurationsmodus → Zählung stoppen
            if current_mode == "config" and last_mode != "config":
                print("[INFO] Konfigurationsmodus erkannt – stoppe Zählung...")
                stop_counter()

            # Zählmodus → Zählung neu starten
            if current_mode == "counting" and last_mode != "counting":
                print("[INFO] Zählmodus erkannt – starte Zählung neu...")
                start_counter()

            last_mode = current_mode

    except KeyboardInterrupt:
        print("\n[INFO] STRG+C erkannt. Beende...")
    finally:
        cleanup()


if __name__ == "__main__":
    main()