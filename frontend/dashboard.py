import streamlit as st
import os
import sys
from PIL import Image, ImageDraw
import json
import sqlite3
import pandas as pd
import altair as alt
from streamlit_drawable_canvas import st_canvas

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
DATA_DIR = os.path.join(ROOT_DIR, "data")
CONFIG_PATH = os.path.join(BACKEND_DIR, "config", "bbox_config.json")
DB_PATH = os.path.join(DATA_DIR, "log.db")
IMAGE_PATH = os.path.join(STATIC_DIR, "last_config.jpg")

sys.path.append(BACKEND_DIR)
sys.path.append(os.path.join(ROOT_DIR, "frontend"))

from camera_interface import capture_image
from components import show_live_counts, show_count_history

# ─── DB initialisieren ───
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log (
            timestamp TEXT,
            in_count INTEGER,
            out_count INTEGER,
            current_count INTEGER,
            total_tracks INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ─── Layout ───
st.set_page_config(page_title="EKSPAR", layout="wide")
st.title("EKSPAR – Live Dashboard")

page = st.sidebar.radio("Navigation", ["📈 Live Dashboard", "📷 Konfiguration"])

# ─── Live Dashboard ───
if page == "📈 Live Dashboard":
    show_live_counts()

    st.markdown("---")
    st.markdown("📈 Verlauf – Personen im Raum")

    st.sidebar.markdown("### 🔎 Zeitfilter")
    time_filter = st.sidebar.selectbox("Zeitraum", ["Letzte 10 Minuten", "Letzte Stunde", "Letzte 24 Stunden", "Alle"])

    now = pd.Timestamp.now()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM log", conn)
        conn.close()

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        if time_filter == "Letzte 10 Minuten":
            df = df[df["timestamp"] >= now - pd.Timedelta(minutes=10)]
        elif time_filter == "Letzte Stunde":
            df = df[df["timestamp"] >= now - pd.Timedelta(hours=1)]
        elif time_filter == "Letzte 24 Stunden":
            df = df[df["timestamp"] >= now - pd.Timedelta(hours=24)]

        show_count_history(df)

    except Exception as e:
        st.warning(f"Fehler beim Laden des Verlaufs: {e}")

# ─── Konfigurationsseite ───
elif page == "📷 Konfiguration":
    st.header("📷 EKSPAR – Konfigurationsmodus")

    edit_mode = st.session_state.get("edit_mode", False)

    if not edit_mode:
        if os.path.exists(IMAGE_PATH):
            img = Image.open(IMAGE_PATH).convert("RGB")
            display_width = 720
            display_height = int(img.height * (display_width / img.width))
            resized_img = img.resize((display_width, display_height))
            draw_img = resized_img.copy()

            has_box = False
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    box = json.load(f)
                    draw = ImageDraw.Draw(draw_img)
                    scale_x = display_width / img.width
                    scale_y = display_height / img.height
                    draw.rectangle([
                        (int(box["x"] * scale_x), int(box["y"] * scale_y)),
                        (int((box["x"] + box["w"]) * scale_x), int((box["y"] + box["h"]) * scale_y))
                    ], outline="#007BFF", width=3)
                    has_box = True

            st.image(draw_img, caption="Aufgenommenes Bild mit Zählbereich", width=display_width)

            if st.button("🖑 Neue Konfiguration starten"):
                st.session_state.edit_mode = True
                if os.path.exists(CONFIG_PATH):
                    os.remove(CONFIG_PATH)
                st.rerun()
        else:
            st.warning("Noch kein Bild vorhanden. Bitte zuerst ein neues Bild aufnehmen.")

    else:
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

            canvas_result = st_canvas(
                fill_color="rgba(0, 123, 255, 0.3)",
                stroke_width=3,
                stroke_color="#007BFF",
                background_image=img,
                update_streamlit=True,
                height=int(img.height * (720 / img.width)),
                width=720,
                drawing_mode="rect",
                key="canvas_edit_mode"
            )

            if st.button("📂 Konfiguration speichern", key="save_button_edit_mode"):
                if canvas_result.json_data and canvas_result.json_data["objects"]:
                    obj = canvas_result.json_data["objects"][-1]
                    bbox = {
                        "x": int(obj["left"] * (img.width / 720)),
                        "y": int(obj["top"] * (img.height / int(img.height * (720 / img.width)))),
                        "w": int(obj["width"] * (img.width / 720)),
                        "h": int(obj["height"] * (img.height / int(img.height * (720 / img.width))))
                    }
                    with open(CONFIG_PATH, "w") as f:
                        json.dump(bbox, f, indent=2)
                    st.success("Konfiguration wurde gespeichert. Zurück zur Ansicht.")
                    st.session_state.edit_mode = False
                    st.rerun()
                else:
                    st.error("❌ Kein Zählbereich markiert. Bitte zuerst ein Rechteck einzeichnen.")
        else:
            st.warning("Kein Bild gefunden. Bitte zuerst ein Bild aufnehmen.")
