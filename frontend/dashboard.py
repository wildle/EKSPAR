# frontend/dashboard.py
"""
Streamlit-Dashboard des EKSPAR-Systems.
Bietet zwei Modi: Live-Personenzählung & visuelle Konfiguration.
"""

# ─── Standardbibliotheken ──────────────────────────────────────────────────────
import os
import sys
import json
import sqlite3

# ─── Drittanbieter-Bibliotheken ────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import altair as alt
from PIL import Image, ImageDraw

# ─── Eigene Module ─────────────────────────────────────────────────────────────
from backend.camera.camera_interface import capture_image
from frontend import components

# ─── Systempfade und Konstanten ────────────────────────────────────────────────
st.set_page_config(page_title="EKSPAR", layout="wide")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')

DB_PATH = os.path.join(DATA_DIR, 'log.db')
CONFIG_PATH = os.path.join(PROJECT_DIR, 'backend', 'config', 'bbox_config.json')
DIRECTION_PATH = os.path.join(PROJECT_DIR, 'backend', 'config', 'direction_config.json')
IMAGE_PATH = os.path.join(STATIC_DIR, 'last_config.jpg')

# ─── Sicherheitsprüfung ───
if "step" not in st.session_state and (not os.path.exists(CONFIG_PATH) or not os.path.exists(DIRECTION_PATH)):
    st.warning("⚠️ Keine Konfiguration vorhanden – bitte starten Sie die Einrichtung.")
    st.session_state.step = 1


# ────────────────────────────────────────────────────────────────────────────────
# 🗃 Datenbank-Initialisierung
# ────────────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """
    Erstellt (falls nötig) die SQLite-Datenbank mit Tabelle für Zähldaten.
    """
    try:
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
    except Exception as e:
        st.error("❌ Fehler beim Initialisieren der Datenbank.")
        st.exception(e)

# ─── Init ───
init_db()

# ─── UI-Stil ───
st.markdown("""
    <style>
        .big-metric {
            font-size: 1.6em;
            font-weight: bold;
            margin-top: 0.25em;
        }
    </style>
""", unsafe_allow_html=True)

# ─── Seitennavigation ───
st.title("EKSPAR – Live Dashboard")
page = st.sidebar.radio("Navigation", ["📈 Live Dashboard", "📷 Konfiguration"])

# ────────────────────────────────────────────────────────────────────────────────
# 📈 Live-Modus: Daten laden & visualisieren
# ────────────────────────────────────────────────────────────────────────────────
if page == "📈 Live Dashboard":
    components.show_live_counts()

    st.markdown("---")
    st.markdown("## 📈 Verlauf – Personen im Raum")

    st.sidebar.markdown("### 🔎 Zeitfilter")
    time_filter = st.sidebar.selectbox(
        "Zeitraum",
        ["Heute", "Gestern", "Letzte Woche", "Letzter Monat", "Letztes Jahr", "Insgesamt"]
    )

    now = pd.Timestamp.now().tz_localize(None)

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM log", conn)
        conn.close()

        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%dT%H:%M:%S.%f", errors="coerce")
        df = df.sort_values("timestamp")

        if time_filter == "Heute":
            df = df[df["timestamp"].dt.date == now.date()]
        elif time_filter == "Gestern":
            df = df[df["timestamp"].dt.date == (now - pd.Timedelta(days=1)).date()]
        elif time_filter == "Letzte Woche":
            df = df[df["timestamp"] >= now - pd.Timedelta(days=7)]
        elif time_filter == "Letzter Monat":
            df = df[df["timestamp"] >= now - pd.DateOffset(months=1)]
        elif time_filter == "Letztes Jahr":
            df = df[df["timestamp"] >= now - pd.DateOffset(years=1)]

        df = components.apply_dynamic_aggregation(df, time_filter)
        df["in_delta"] = df["in_count"].diff().fillna(df["in_count"]).clip(lower=0)
        total_people = int(df["in_delta"].sum())


        # Dynamische Textausgabe (sprachlich korrekt)
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

        components.show_count_history(df, time_filter)

        if not df.empty:
            if time_filter in ["Heute", "Gestern", "Letzte Woche"]:
                st.altair_chart(components.show_hourly_distribution(df), use_container_width=True)

            if time_filter in ["Letzte Woche", "Letzter Monat", "Insgesamt"]:
                st.altair_chart(components.show_daily_average(df), use_container_width=True)

        st.download_button(
            label="📤 CSV-Export starten",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"ekpsar_export_{time_filter.lower().replace(' ', '_')}.csv",
            mime="text/csv"
        )

        st.caption("Exportiert die aggregierten Zähldaten im CSV-Format.")

    except Exception as e:
        st.error("❌ Fehler beim Laden oder Verarbeiten der Verlaufsdaten.")
        st.info("📌 Bitte prüfe die Datenbankverbindung, Zeitfilter oder exportierte Dateien.")
        st.exception(e)

# ────────────────────────────────────────────────────────────────────────────────
# 🧭 Konfigurationsmodus
# ────────────────────────────────────────────────────────────────────────────────
elif page == "📷 Konfiguration":
    if st.session_state.get("last_page") != page:
        st.session_state.last_page = page
        st.session_state.pop("step", None)
        st.rerun()

    st.session_state.setdefault("bbox", None)
    st.session_state.setdefault("direction", [])

    if "step" not in st.session_state:
        components.show_config_overview()
        st.stop()

    step = st.session_state.step
    components.draw_instruction_step(step)

    if step == 1:
        components.draw_capture_ui_step()
    elif step == 2:
        components.draw_bbox_ui_step()
    elif step == 3:
        components.draw_direction_ui_step()
    elif step == 4:
        components.draw_overview_and_save()


