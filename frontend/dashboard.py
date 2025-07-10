import streamlit as st
import os
import sys
import json
import sqlite3
import pandas as pd
import altair as alt
from PIL import Image, ImageDraw

# ─── Layout ───
st.set_page_config(page_title="EKSPAR", layout="wide")

# 🛠 Systempfad erweitern, damit backend und frontend erkannt werden
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 🛠 Projektpfade definieren
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')
DB_PATH = os.path.join(DATA_DIR, 'log.db')
CONFIG_PATH = os.path.join(PROJECT_DIR, 'backend', 'config', 'bbox_config.json')
DIRECTION_PATH = os.path.join(PROJECT_DIR, 'backend', 'config', 'direction_config.json')
IMAGE_PATH = os.path.join(STATIC_DIR, 'last_config.jpg')

# 🛠 Eigene Module importieren
from backend.camera.camera_interface import capture_image
from frontend.components import show_live_counts, show_count_history, show_hourly_distribution, show_daily_average, apply_dynamic_aggregation

# ─── Sicherheitsprüfung ───
if "step" not in st.session_state and (not os.path.exists(CONFIG_PATH) or not os.path.exists(DIRECTION_PATH)):
    st.warning("⚠️ Keine Konfiguration vorhanden – bitte starten Sie die Einrichtung.")
    st.session_state.step = 1


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

# ─── Initialisieren ───
init_db()

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

    now = pd.Timestamp.now().tz_localize(None)  # explizit lokal und naive

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM log", conn)
        conn.close()

        
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%dT%H:%M:%S.%f", errors="coerce")
        df = df.sort_values("timestamp")

        print("[DEBUG] now =", now)
        print("[DEBUG] df timestamps (tail):", df["timestamp"].tail().tolist())

        if time_filter == "Heute":
            df = df[df["timestamp"].dt.normalize() == now.normalize()]
        elif time_filter == "Gestern":
            df = df[df["timestamp"].dt.date == (now - pd.Timedelta(days=1)).date()]
        elif time_filter == "Letzte Woche":
            # df = df[df["timestamp"] >= now - pd.Timedelta(weeks=1)]
            week_ago = now - pd.Timedelta(days=7)
            df = df[df["timestamp"] >= week_ago]
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

        show_count_history(df, time_filter) # optional y_axis_step


        
        if time_filter in ["Heute", "Gestern", "Letzte Woche"]:
            st.altair_chart(show_hourly_distribution(df), use_container_width=True)

        if time_filter in ["Letzte Woche", "Letzter Monat", "Insgesamt"]:
            st.altair_chart(show_daily_average(df), use_container_width=True)

        # CSV-Export für alle Zeiträume
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📤 CSV-Export starten",
            data=csv,
            file_name=f"ekpsar_export_{time_filter.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )

        st.caption("Exportiert die aggregierten Zähldaten im CSV-Format.")
        

    except Exception as e:
        st.warning(f"Fehler beim Laden des Verlaufs: {e}")

# ─── Konfigurationsmodus ───
elif page == "📷 Konfiguration":
    # Bei Seitenwechsel ggf. "step" zurücksetzen, damit Übersicht angezeigt wird
    if "last_page" not in st.session_state or st.session_state.last_page != page:
        if "step" in st.session_state:
            del st.session_state["step"]
        st.session_state.last_page = page
        st.rerun()

    from frontend import components  # falls noch nicht importiert

    # ─── Session-State initialisieren ───
    if "bbox" not in st.session_state:
        st.session_state.bbox = None
    if "direction" not in st.session_state:
        st.session_state.direction = []

    # ⬅️ Zeige Konfigurationsübersicht beim ersten Aufruf
    if "step" not in st.session_state:
        from frontend.components import show_config_overview
        show_config_overview()
        st.stop()  # Verhindert, dass die Schritte unten ausgeführt werden

    # ─── Hauptlogik je nach Schritt ───
    step = st.session_state.step
    components.draw_instruction_step(step)

    if step == 1:
        show = False
        if st.button("📷 Bild aufnehmen"):
            with st.spinner("Kamera wird aktiviert..."):
                success = capture_image()
            if success:
                st.success("Bild erfolgreich aufgenommen.")
                st.session_state.image_updated = True
                show = True

        if st.session_state.get("image_updated", False) or os.path.exists(IMAGE_PATH):
            try:
                img = components.load_image_fresh(IMAGE_PATH)
                st.image(img, caption="📸 Aufgenommenes Bild", width=1280)
            except Exception as e:
                st.error(f"Bild konnte nicht geladen werden: {e}")

        if os.path.exists(IMAGE_PATH):
            if st.button("➡ Weiter zu Schritt 2"):
                st.session_state.step = 2
                st.session_state.image_updated = False
                st.rerun()

    elif step == 2:
        components.draw_bbox_ui_step()

    elif step == 3:
        components.draw_direction_ui_step()

    elif step == 4:
        components.draw_overview_and_save()

