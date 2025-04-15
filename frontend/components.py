import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import json
import os

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CONFIG_PATH = os.path.join(ROOT_DIR, "backend", "config", "bbox_config.json")
IMAGE_PATH = os.path.join(ROOT_DIR, "static", "last_config.jpg")
COUNTER_PATH = os.path.join(ROOT_DIR, "data", "counter.json")

# ─── Funktionen ───
def load_bbox():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return None

def save_bbox(bbox):
    with open(CONFIG_PATH, "w") as f:
        json.dump(bbox, f)
    st.success("Bounding Box gespeichert.")

def draw_bbox_ui():
    st.markdown("### Schritt 2: Zähldetektion – Türbereich markieren")
    st.markdown("##### Bereich markieren")

    if not os.path.exists(IMAGE_PATH):
        st.warning("Bitte zuerst ein Bild aufnehmen.")
        return

    try:
        bg_image = Image.open(IMAGE_PATH)
    except Exception as e:
        st.error(f"Fehler beim Laden des Bildes: {e}")
        return

    # Zeichenfläche mittig ausrichten
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 0.3)",
            stroke_width=2,
            background_image=bg_image,
            update_streamlit=True,
            height=720,
            width=1280,
            drawing_mode="rect",
            key="canvas"
        )

    # Letztes Rechteck speichern
    if canvas_result.json_data and canvas_result.json_data["objects"]:
        obj = canvas_result.json_data["objects"][-1]
        left = int(obj["left"])
        top = int(obj["top"])
        width = int(obj["width"])
        height = int(obj["height"])
        bbox = {"x": left, "y": top, "w": width, "h": height}

        if st.button("✅ Bounding Box speichern"):
            save_bbox(bbox)

    # Gespeicherte Box anzeigen
    saved = load_bbox()
    if saved:
        st.info(
            f"Gespeicherte Box: \U0001f7aa x={saved['x']}, y={saved['y']}, w={saved['w']}, h={saved['h']}"
        )

def show_live_counts():
    st.markdown("### 📊 Live-Zähler")

    if not os.path.exists(COUNTER_PATH):
        st.warning("Zählerdatei nicht gefunden.")
        return

    try:
        with open(COUNTER_PATH, "r") as f:
            data = json.load(f)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 IN", data.get("in", 0))
        col2.metric("🚪 OUT", data.get("out", 0))
        col3.metric("🟢 Aktuell", data.get("current", 0))
        col4.metric("🧠 Tracks", data.get("total_tracks", 0))

        st.caption(f"Aktualisiert: {data.get('timestamp', 'unbekannt')}")
    except Exception as e:
        st.error(f"Fehler beim Laden der Zähldaten: {e}")
