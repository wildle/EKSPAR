import streamlit as st
import os
import sys
from PIL import Image
import json
import time
import sqlite3
import pandas as pd
import altair as alt

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
DATA_DIR = os.path.join(ROOT_DIR, "data")
CONFIG_PATH = os.path.join(ROOT_DIR, "backend", "config", "bbox_config.json")
DB_PATH = os.path.join(DATA_DIR, "log.db")

IMAGE_PATH = os.path.join(STATIC_DIR, "last_config.jpg")

# sys.path erweitern, damit Backend-Import funktioniert
sys.path.append(BACKEND_DIR)
sys.path.append(os.path.join(ROOT_DIR, "frontend"))

from camera_interface import capture_image
from streamlit_drawable_canvas import st_canvas
from components import show_live_counts

# Layout
st.set_page_config(page_title="EKSPAR", layout="wide")
st.title("EKSPAR – Dashboard")

# Seitenwahl
page = st.sidebar.radio("Navigation", ["📷 Konfiguration", "📈 Live Dashboard"])

if page == "📷 Konfiguration":
    st.header("📷 EKSPAR – Konfigurationsmodus")
    st.markdown("### Schritt 1: Einzelbild aufnehmen")

    if st.button("📷 Neues Bild aufnehmen"):
        with st.spinner("Kamera aktiviert..."):
            success = capture_image()
        if success:
            st.success("Bild erfolgreich aufgenommen!")
        else:
            st.error("Fehler beim Aufnehmen des Bildes.")

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

elif page == "📈 Live Dashboard":
    st.header("📈 EKSPAR – Live-Zähler & Verlauf")
    st.markdown("## 📊 Live-Zählerstand")
    show_live_counts()

    st.markdown("---")
    st.markdown("## 📈 Verlauf der Zählwerte")

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM log ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("timestamp:T", title="Zeit"),
            y=alt.Y("current_count:Q", title="Aktuell im Raum"),
            tooltip=["timestamp", "in_count", "out_count", "current_count", "total_tracks"]
        ).properties(
            height=300,
            title="🕓 Personen im Raum (Verlauf)"
        )

        st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.warning(f"Fehler beim Laden des Verlaufs: {e}")
