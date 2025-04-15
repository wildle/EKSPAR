import streamlit as st
import os
import sys
from PIL import Image
import json
import time

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
CONFIG_PATH = os.path.join(ROOT_DIR, "backend", "config", "bbox_config.json")

IMAGE_PATH = os.path.join(STATIC_DIR, "last_config.jpg")

# sys.path erweitern, damit Backend-Import funktioniert
sys.path.append(BACKEND_DIR)
sys.path.append(os.path.join(ROOT_DIR, "frontend"))

from camera_interface import capture_image
from streamlit_drawable_canvas import st_canvas
from components import show_live_counts

# Layout
st.set_page_config(page_title="EKSPAR – Konfiguration", layout="wide")
st.title("📷 EKSPAR – Konfigurationsmodus")

st.markdown("### Schritt 1: Einzelbild aufnehmen")

# Bild aufnehmen
if st.button("📷 Neues Bild aufnehmen"):
    with st.spinner("Kamera aktiviert..."):
        success = capture_image()
    if success:
        st.success("Bild erfolgreich aufgenommen!")
    else:
        st.error("Fehler beim Aufnehmen des Bildes.")

# Bild anzeigen + Bounding Box UI
if os.path.exists(IMAGE_PATH):
    img = Image.open(IMAGE_PATH)
    st.image(img, caption="Aufgenommenes Bild", width=720)

    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=3,
        stroke_color="#FF0000",
        background_image=img,
        update_streamlit=True,
        height=int(img.height * (720 / img.width)),
        width=720,
        drawing_mode="rect",
        key="canvas",
    )

    if canvas_result.json_data is not None:
        for obj in canvas_result.json_data["objects"]:
            if obj["type"] == "rect":
                left = int(obj["left"])
                top = int(obj["top"])
                width = int(obj["width"])
                height = int(obj["height"])

                bbox = {"x": left, "y": top, "w": width, "h": height}
                with open(CONFIG_PATH, "w") as f:
                    json.dump(bbox, f, indent=2)

                st.success(f"Gespeicherte Box: x={left}, y={top}, w={width}, h={height}")
else:
    st.warning("Noch kein Bild aufgenommen. Bitte zuerst ein Bild erstellen.")

# Live-Zähler anzeigen
st.markdown("---")
st.markdown("## 📊 Live-Zählerstand")
show_live_counts()
