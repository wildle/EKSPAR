import streamlit as st
import altair as alt
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
import json
import os
import math
from datetime import datetime

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CONFIG_PATH = os.path.join(ROOT_DIR, "backend", "config", "bbox_config.json")
IMAGE_PATH = os.path.join(ROOT_DIR, "static", "last_config.jpg")
COUNTER_PATH = os.path.join(ROOT_DIR, "data", "counter.json")
DIRECTION_PATH = os.path.join(ROOT_DIR, "backend", "config", "direction_config.json")
LOCK_PATH = os.path.join(ROOT_DIR, "camera.lock")

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Utility Funktionen
# ────────────────────────────────────────────────────────────────────────────────
def annotate_daytime(hour):
    if 0 <= hour < 6:
        return "🌙 Nacht"
    elif 6 <= hour < 12:
        return "🕖 Morgens"
    elif 12 <= hour < 18:
        return "☀️ Nachmittag"
    else:
        return "🌆 Abends"

def point_inside_bbox(point, bbox):
    x, y = point
    return bbox["x"] <= x <= bbox["x"] + bbox["w"] and bbox["y"] <= y <= bbox["y"] + bbox["h"]

def draw_arrowhead(draw, p1, p2, size=20):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1:
        return
    angle = math.atan2(dy, dx)
    for delta in [150, -150]:
        theta = angle + math.radians(delta)
        x = p2[0] + size * math.cos(theta)
        y = p2[1] + size * math.sin(theta)
        draw.line([p2, (x, y)], fill="red", width=4)

# ────────────────────────────────────────────────────────────────────────────────
# 🟦 Bounding Box Laden / Speichern
# ────────────────────────────────────────────────────────────────────────────────
def load_bbox():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return None

def save_bbox(bbox):
    with open(CONFIG_PATH, "w") as f:
        json.dump(bbox, f)
    st.success("Bounding Box gespeichert.")

# ────────────────────────────────────────────────────────────────────────────────
# 📊 Dashboard – Live-Zähler & Verlauf
# ────────────────────────────────────────────────────────────────────────────────
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

def show_count_history(df, time_filter, y_axis_step=1):
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
    df["current_count"] = df["current_count"].astype(int)

    chart = alt.Chart(df).mark_line(interpolate="monotone").encode(
        x=x_axis,
        y=alt.Y("current_count:Q", title="Personenzahl", scale=alt.Scale(nice=False)),
        tooltip=["timestamp:T", "current_count"]
    ).properties(
        width="container",
        height=300,
        title="👣 Personen im Raum (Verlauf)"
    )

    st.altair_chart(chart, use_container_width=True)

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

# ────────────────────────────────────────────────────────────────────────────────
# 🧭 Konfigurationsmodus – Schrittweises UI (Schritte 1–4)
# ────────────────────────────────────────────────────────────────────────────────
def draw_instruction_step(step):
    step_titles = {
        1: "📷 Bild aufnehmen",
        2: "🟦 Zählbereich definieren",
        3: "➡️ Eintrittsrichtung definieren",
        4: "💾 Konfiguration bestätigen"
    }
    st.markdown(f"## 🧭 Konfiguration: Schritt {step} – {step_titles.get(step, 'Unbekannt')}")

    instructions = {
        1: "📷 Bitte ein neues Bild aufnehmen.",
        2: "🟦 Markiere den Zählbereich in Form eines Rechtecks.",
        3: "➡️ Wähle, aus welcher Richtung Personen den Raum **betreten**.",
        4: "💾 Überprüfe und speichere die Konfiguration."
    }
    st.info(instructions.get(step, "Unbekannter Schritt."))

def draw_bbox_ui_step():
    if not os.path.exists(IMAGE_PATH):
        st.warning("❌ Kein Bild gefunden. Bitte zuerst ein Bild aufnehmen (Schritt 1).")
        return
    try:
        bg_image = Image.open(IMAGE_PATH)
    except Exception as e:
        st.error(f"Fehler beim Laden des Bildes: {e}")
        return

    canvas_result = st_canvas(
        fill_color="rgba(0, 123, 255, 0.3)",
        stroke_width=3,
        stroke_color="#007BFF",
        background_image=bg_image,
        update_streamlit=True,
        height=720,
        width=1280,
        drawing_mode="rect",
        key="bbox_step"
    )

    if canvas_result.json_data and canvas_result.json_data["objects"]:
        obj = canvas_result.json_data["objects"][-1]
        bbox = {
            "x": int(obj["left"]),
            "y": int(obj["top"]),
            "w": int(obj["width"]),
            "h": int(obj["height"])
        }
        if st.button("✅ Bounding Box speichern und weiter"):
            save_bbox(bbox)
            st.session_state.bbox = bbox
            st.session_state.step = 3
            st.rerun()

    saved = load_bbox()
    if saved:
        st.success("✅ Zählbereich wurde erfolgreich gespeichert.")

def draw_direction_ui_step():
    st.markdown("### ➡️ Eintrittsrichtung definieren")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ Eintritt von links nach rechts"):
            st.session_state.direction = {"entry": "left_to_right", "angle": 0}
            st.session_state.step = 4
            st.rerun()
    with col2:
        if st.button("⬅️ Eintritt von rechts nach links"):
            st.session_state.direction = {"entry": "right_to_left", "angle": 180}
            st.session_state.step = 4
            st.rerun()
    draw_bbox_preview_only()

def draw_bbox_preview_only():
    if not os.path.exists(IMAGE_PATH) or "bbox" not in st.session_state:
        return
    try:
        img = Image.open(IMAGE_PATH).convert("RGB").copy()
        draw = ImageDraw.Draw(img)
        box = st.session_state.bbox
        draw.rectangle(
            [(box["x"], box["y"]), (box["x"] + box["w"], box["y"] + box["h"])],
            outline="blue", width=4
        )
        st.image(img, caption="Zählbereich-Vorschau", width=1280)
    except Exception:
        pass

def draw_overview_and_save():
    if not os.path.exists(IMAGE_PATH):
        st.warning("❌ Kein Bild gefunden.")
        return
    if "bbox" not in st.session_state or "direction" not in st.session_state:
        st.error("❌ Bounding Box oder Richtung fehlt.")
        return
    try:
        img = Image.open(IMAGE_PATH).convert("RGB").copy()
        draw = ImageDraw.Draw(img)
        box = st.session_state.bbox
        draw.rectangle(
            [(box["x"], box["y"]), (box["x"] + box["w"], box["y"] + box["h"])],
            outline="blue", width=4
        )
        entry = st.session_state.direction["entry"]
        p1, p2 = ((100, 360), (1180, 360)) if entry == "left_to_right" else ((1180, 360), (100, 360))
        draw.line([p1, p2], fill="red", width=5)
        draw_arrowhead(draw, p1, p2)
        r = 10
        draw.ellipse((p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r), fill="green")
        st.success(f"{'➡️' if entry == 'left_to_right' else '⬅️'} Eintrittsrichtung: {entry.replace('_', ' ')}")
        st.image(img, caption="Vorschau: Zählbereich + Richtungspfeil", width=1280)
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))
        if st.button("💾 Konfiguration speichern & System starten"):
            with open(DIRECTION_PATH, "w") as f:
                json.dump({"entry": entry, "angle": angle}, f, indent=2)
            with open(LOCK_PATH, "w") as f:
                f.write("counting")
            st.success("✅ Konfiguration gespeichert. Zählung gestartet.")
            st.session_state.step = 1
            st.session_state.bbox = None
            st.session_state.direction = []
            st.rerun()
    except Exception as e:
        st.error(f"Fehler beim Zeichnen/Speichern: {e}")

def show_config_overview():
    st.markdown("## 🧭 Konfiguration")
    bbox = load_bbox()
    if not bbox or not os.path.exists(DIRECTION_PATH):
        st.info("ℹ️ Noch keine vollständige Konfiguration vorhanden.")
        return
    try:
        img = Image.open(IMAGE_PATH).convert("RGB").copy()
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [(bbox["x"], bbox["y"]), (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"])],
            outline="blue", width=4
        )
        with open(DIRECTION_PATH, "r") as f:
            direction = json.load(f)
        p1, p2 = ((100, 360), (1180, 360)) if direction["entry"] == "left_to_right" else ((1180, 360), (100, 360))
        draw.line([p1, p2], fill="red", width=5)
        draw_arrowhead(draw, p1, p2)
        r = 10
        draw.ellipse((p1[0]-r, p1[1]-r, p1[0]+r, p1[1]+r), fill="green")
        st.image(img, caption="Aktuelle Konfiguration", width=1280)
    except Exception as e:
        st.error(f"Fehler beim Laden der Übersicht: {e}")
    if st.button("🔁 Neue Konfiguration starten"):
        st.session_state.step = 1
        st.session_state.bbox = None
        st.session_state.direction = []
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
        if os.path.exists(DIRECTION_PATH):
            os.remove(DIRECTION_PATH)
        st.rerun()