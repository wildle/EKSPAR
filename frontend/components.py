import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import json
import os

CONFIG_PATH = "config/bbox_config.json"
IMAGE_PATH = "static/last_config.jpg"

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

    if not os.path.exists(IMAGE_PATH):
        st.warning("Bitte zuerst ein Bild aufnehmen.")
        return

    # Bild mit PIL laden
    try:
        bg_image = Image.open(IMAGE_PATH)
    except Exception as e:
        st.error(f"Fehler beim Laden des Bildes: {e}")
        return

    # Zeichenfläche
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=2,
        background_image=bg_image,
        update_streamlit=True,
        height=480,
        width=720,
        drawing_mode="rect",
        key="canvas"
    )

    # Letztes gezeichnetes Rechteck verwenden
    if canvas_result.json_data and canvas_result.json_data["objects"]:
        obj = canvas_result.json_data["objects"][-1]  # letzte Box
        left = int(obj["left"])
        top = int(obj["top"])
        width = int(obj["width"])
        height = int(obj["height"])
        bbox = {"x": left, "y": top, "w": width, "h": height}

        if st.button("✅ Bounding Box speichern"):
            save_bbox(bbox)

    # Zeige gespeicherte Box, falls vorhanden
    saved = load_bbox()
    if saved:
        st.info(
            f"Gespeicherte Box:\n"
            f"🔲 x={saved['x']}, y={saved['y']}, w={saved['w']}, h={saved['h']}"
        )
