import streamlit as st
import altair as alt
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import json
import os
from datetime import datetime

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CONFIG_PATH = os.path.join(ROOT_DIR, "backend", "config", "bbox_config.json")
IMAGE_PATH = os.path.join(ROOT_DIR, "static", "last_config.jpg")
COUNTER_PATH = os.path.join(ROOT_DIR, "data", "counter.json")

# ─── Bounding Box Funktionen ───
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

    if canvas_result.json_data and canvas_result.json_data["objects"]:
        obj = canvas_result.json_data["objects"][-1]
        left = int(obj["left"])
        top = int(obj["top"])
        width = int(obj["width"])
        height = int(obj["height"])
        bbox = {"x": left, "y": top, "w": width, "h": height}

        if st.button("✅ Bounding Box speichern"):
            save_bbox(bbox)

    saved = load_bbox()
    if saved:
        st.info(f"Gespeicherte Box: \U0001f7aa x={saved['x']}, y={saved['y']}, w={saved['w']}, h={saved['h']}")

# ─── Live-Zähleranzeige ───
def show_live_counts():
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

        timestamp = data.get("timestamp")
        if timestamp:
            ts = datetime.fromisoformat(timestamp)
            st.caption(f"Aktualisiert: {ts.strftime('%Y-%m-%dT%H:%M:%S.%f')}")
        else:
            st.caption("Kein Zeitstempel verfügbar")

    except Exception as e:
        st.error(f"Fehler beim Laden der Zähldaten: {e}")

# ─── Chartanzeige ───
def show_count_history(df, time_filter, y_axis_step=1):

    # Dynamische Achsenformatierung basierend auf Zeitraum
    if time_filter in ["Heute", "Gestern"]:
        x_format = "%H:%M"
        tick_count = "hour"
    elif time_filter in ["Letzte Woche", "Letzter Monat"]:
        x_format = "%d.%m."
        tick_count = "day"
    elif time_filter in ["Letztes Jahr", "Insgesamt"]:
        x_format = "%b %Y"
        tick_count = "month"
    else:
        x_format = "%d.%m."
        tick_count = "day"

    x_axis = alt.X(
        "timestamp:T",
        title="Zeit",
        axis=alt.Axis(format=x_format, tickCount=tick_count, labelAngle=0)
    )

    if df.empty:
        st.info("Keine Daten für den ausgewählten Zeitraum.")
        return

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # ─── Aktuelle Werte runden ───
    df["current_count"] = df["current_count"].astype(int)

    # ─── Tageszeit-Klassifikation ───
    def annotate_daytime(hour):
        if 0 <= hour < 6:
            return "🌙 Nacht"
        elif 6 <= hour < 12:
            return "🕖 Morgens"
        elif 12 <= hour < 18:
            return "☀️ Nachmittag"
        else:
            return "🌆 Abends"

    df["daytime"] = df["timestamp"].dt.hour.apply(annotate_daytime)

    # ─── Maxwert für Marker ermitteln ───
    peak_row = df.loc[df["current_count"].idxmax()]
    peak_point = pd.DataFrame([{
        "timestamp": peak_row["timestamp"],
        "current_count": peak_row["current_count"],
        "label": f"⏱ Höchstwert: {peak_row['current_count']} Personen ({peak_row['timestamp'].strftime('%H:%M')})"
    }])

    # ─── Hauptchart ───
    chart = alt.Chart(df).mark_area(
        interpolate="monotone",
        line={"color": "#1f77b4"},
        color=alt.Gradient(
            gradient="linear",
            stops=[alt.GradientStop(color="#1f77b440", offset=0), alt.GradientStop(color="#1f77b400", offset=1)],
            x1=1, x2=1, y1=1, y2=0
        )
    ).encode(
        x=x_axis,
        y=alt.Y("current_count:Q", title="Personen im Raum", axis=alt.Axis(tickMinStep=1, format=".0f")),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Zeitpunkt"),
            alt.Tooltip("current_count:Q", title="Anzahl"),
            alt.Tooltip("daytime:N", title="Tageszeit")
        ]
    ).properties(
        height=300,
        title="🕓 Personen im Raum (Verlauf)"
    )

    # ─── Max-Wert markieren ───
    peak = alt.Chart(peak_point).mark_point(
        shape="circle",
        size=80,
        color="red"
    ).encode(
        x="timestamp:T",
        y="current_count:Q",
        tooltip="label:N"
    )

    st.altair_chart(chart + peak, use_container_width=True)

def show_hourly_distribution(df):
    df["hour"] = df["timestamp"].dt.hour
    hourly = df.groupby("hour")["in_delta"].sum().reset_index()

    chart = alt.Chart(hourly).mark_bar().encode(
        x=alt.X("hour:O", title="Stunde des Tages", sort=list(range(24))),
        y=alt.Y("in_delta:Q", title="Personenanzahl"),
        tooltip=["hour", "in_delta"]
    ).properties(
        width="container",
        height=300,
        title="📊 Personen pro Stunde"
    )

    return chart    

def show_daily_average(df):
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["time"] = df["timestamp"].dt.strftime("%H:%M")
    
    if "in_delta" not in df.columns:
        df["in_delta"] = df["in_count"].diff().fillna(df["in_count"]).clip(lower=0)

    daily_avg = df.groupby("time")["in_delta"].mean().reset_index()
    daily_avg["in_delta"] = daily_avg["in_delta"].round(2)

    chart = alt.Chart(daily_avg).mark_line(
        point=True,
        interpolate="monotone"
    ).encode(
        x=alt.X("time:O", title="Uhrzeit", sort="ascending"),
        y=alt.Y("in_delta:Q", title="Ø Personen pro Zeitfenster"),
        tooltip=["time", "in_delta"]
    ).properties(
        title="📈 Durchschnittlicher Tagesverlauf",
        height=300
    )

    return chart
