import streamlit as st
import os
import sys
import json
import sqlite3
import pandas as pd
import altair as alt
from PIL import Image, ImageDraw

# 🛠 Systempfad erweitern, damit backend und frontend erkannt werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 🛠 Projektpfade definieren
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')
DB_PATH = os.path.join(DATA_DIR, 'log.db')
CONFIG_PATH = os.path.join(PROJECT_DIR, 'backend', 'config', 'bbox_config.json')
IMAGE_PATH = os.path.join(STATIC_DIR, 'last_config.jpg')

# 🛠 Eigene Module importieren
from backend.camera.camera_interface import capture_image
from frontend.components import show_live_counts, show_count_history

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

# ─── Dynamische Aggregation ───
def apply_dynamic_aggregation(df, time_filter):
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    if time_filter == "Heute":
        df["rounded_time"] = df["timestamp"].dt.floor("10min")
    elif time_filter == "Gestern":
        df["rounded_time"] = df["timestamp"].dt.floor("30min")
    elif time_filter == "Letzte Woche":
        df["rounded_time"] = df["timestamp"].dt.floor("1h")
    elif time_filter == "Letzter Monat":
        df["rounded_time"] = df["timestamp"].dt.floor("1d")
    elif time_filter == "Letztes Jahr":
        df["rounded_time"] = df["timestamp"].dt.to_period("W").dt.start_time
    elif time_filter == "Insgesamt":
        df["rounded_time"] = df["timestamp"].dt.to_period("M").dt.start_time
    else:
        df["rounded_time"] = df["timestamp"]

    df = df.groupby("rounded_time").agg({
        "in_count": "max",
        "out_count": "max",
        "current_count": "max",
        "total_tracks": "max"
    }).reset_index()

    df.rename(columns={"rounded_time": "timestamp"}, inplace=True)
    df["current_count"] = df["current_count"].round().astype(int)

    return df

# ─── Initialisieren ───
init_db()

# ─── Layout ───
st.set_page_config(page_title="EKSPAR", layout="wide")

st.markdown("""
    <style>
        .big-metric {
            font-size: 1.6em;
            font-weight: bold;
            margin-top: 0.25em;
        }
    </style>
""", unsafe_allow_html=True)

st.title("EKSPAR – Live Dashboard")

page = st.sidebar.radio("Navigation", ["📈 Live Dashboard", "📷 Konfiguration"])

# ─── Live Dashboard ───
if page == "📈 Live Dashboard":
    show_live_counts()

    st.markdown("---")
    st.markdown("## 📈 Verlauf – Personen im Raum")

    st.sidebar.markdown("### 🔎 Zeitfilter")
    time_filter = st.sidebar.selectbox("Zeitraum", ["Heute", "Gestern", "Letzte Woche", "Letzter Monat", "Letztes Jahr", "Insgesamt"])

    now = pd.Timestamp.now()
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM log", conn)
        conn.close()

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        if time_filter == "Heute":
            df = df[df["timestamp"].dt.date == now.date()]
        elif time_filter == "Gestern":
            df = df[df["timestamp"].dt.date == (now - pd.Timedelta(days=1)).date()]
        elif time_filter == "Letzte Woche":
            df = df[df["timestamp"] >= now - pd.Timedelta(weeks=1)]
        elif time_filter == "Letzter Monat":
            df = df[df["timestamp"] >= now - pd.DateOffset(months=1)]
        elif time_filter == "Letztes Jahr":
            df = df[df["timestamp"] >= now - pd.DateOffset(years=1)]

        df = apply_dynamic_aggregation(df, time_filter)

        df["in_delta"] = df["in_count"].diff().fillna(df["in_count"]).clip(lower=0)
        total_people = int(df["in_delta"].sum())

        filter_text = {
            "Heute": "heute",
            "Gestern": "gestern",
            "Letzte Woche": "in der letzten Woche",
            "Letzter Monat": "im letzten Monat",
            "Letztes Jahr": "im letzten Jahr",
            "Insgesamt": "insgesamt"
        }

        st.markdown(f"""
        <div class="big-metric">👥 {total_people:,} Personen {filter_text.get(time_filter, '')}</div>
        """, unsafe_allow_html=True)

        show_count_history(df, y_axis_step=1)

    except Exception as e:
        st.warning(f"Fehler beim Laden des Verlaufs: {e}")

# ─── Konfigurationsmodus ───
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

            from streamlit_drawable_canvas import st_canvas

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
                    scale_x = img.width / 720
                    scale_y = img.height / int(img.height * (720 / img.width))

                    bbox = {
                        "x": int(obj["left"] * scale_x),
                        "y": int(obj["top"] * scale_y),
                        "w": int(obj["width"] * scale_x),
                        "h": int(obj["height"] * scale_y)
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
