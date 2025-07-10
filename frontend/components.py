import streamlit as st
import altair as alt
import pandas as pd
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
import json
import os
import math
from datetime import datetime
import io
from backend.camera.camera_interface import capture_image

# ─── Pfade setzen ───
CURRENT_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
CONFIG_PATH = os.path.join(ROOT_DIR, "backend", "config", "bbox_config.json")
IMAGE_PATH = os.path.join(ROOT_DIR, "static", "last_config.jpg")
COUNTER_PATH = os.path.join(ROOT_DIR, "data", "counter.json")
DIRECTION_PATH = os.path.join(ROOT_DIR, "backend", "config", "direction_config.json")
LOCK_PATH = os.path.join(ROOT_DIR, "camera.lock")

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Utility Funktionen (Bild laden, Hilfsfunktionen, Pfeile etc.)
# ────────────────────────────────────────────────────────────────────────────────
def load_image_fresh(path):
    """
    Lädt ein Bild unabhängig vom Dateicache.

    Args:
        path (str): Pfad zur Bilddatei.

    Returns:
        PIL.Image.Image: Frisch geladenes Bild.

    Raises:
        FileNotFoundError: Falls die Datei nicht existiert.
        OSError: Falls das Bild nicht geöffnet werden kann.
    """
    try:
        with open(path, "rb") as f:
            return Image.open(io.BytesIO(f.read())).copy()
    except Exception as e:
        raise RuntimeError(f"Bild konnte nicht geladen werden: {e}")


def annotate_daytime(hour: int) -> str:
    """
    Gibt die Tageszeit basierend auf der Stunde zurück.

    Args:
        hour (int): Stunde im 24-Stunden-Format (0–23)

    Returns:
        str: Symbol + Bezeichnung der Tageszeit
    """
    if 0 <= hour < 6:
        return "🌙 Nacht"
    elif 6 <= hour < 12:
        return "🕖 Morgens"
    elif 12 <= hour < 18:
        return "☀️ Nachmittag"
    else:
        return "🌆 Abends"


def point_inside_bbox(point: tuple[int, int], bbox: dict) -> bool:
    """
    Prüft, ob ein Punkt innerhalb einer gegebenen Bounding Box liegt.

    Args:
        point (tuple[int, int]): Punktkoordinaten als (x, y)
        bbox (dict): Bounding Box mit Schlüsseln 'x', 'y', 'w', 'h'

    Returns:
        bool: True, wenn der Punkt innerhalb der Bounding Box liegt, sonst False
    """
    x, y = point
    return (
        bbox["x"] <= x <= bbox["x"] + bbox["w"]
        and bbox["y"] <= y <= bbox["y"] + bbox["h"]
    )


def draw_arrowhead(draw: ImageDraw.ImageDraw, p1: tuple[int, int], p2: tuple[int, int], size: int = 20) -> None:
    """
    Zeichnet Pfeilspitzen an eine Linie (z. B. zur Richtungserkennung).

    Args:
        draw (ImageDraw.ImageDraw): Zeichenobjekt von PIL
        p1 (tuple[int, int]): Startpunkt der Linie
        p2 (tuple[int, int]): Endpunkt der Linie
        size (int, optional): Größe der Pfeilspitzen. Standard ist 20.
    """
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
def load_bbox() -> dict | None:
    """
    Lädt die gespeicherte Bounding Box aus der Konfigurationsdatei.

    Returns:
        dict | None: Bounding Box als Dictionary oder None, falls nicht vorhanden.
    """
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return None


def save_bbox(bbox: dict) -> None:
    """
    Speichert die übergebene Bounding Box in der Konfigurationsdatei.

    Args:
        bbox (dict): Die Bounding Box mit x, y, w, h.
    """
    with open(CONFIG_PATH, "w") as f:
        json.dump(bbox, f)
    st.success("Bounding Box gespeichert.")


# ────────────────────────────────────────────────────────────────────────────────
# 📊 Datenaggregation für Zeitverlauf (Dashboard-Backend)
# ────────────────────────────────────────────────────────────────────────────────

def apply_dynamic_aggregation(df: pd.DataFrame, time_filter: str) -> pd.DataFrame:
    """
    Aggregiert die Zähldaten je nach Zeitfilter für Visualisierungen im Dashboard.

    Args:
        df: DataFrame mit Zeitstempeln und Zähldaten.
        time_filter: Zeitbereichsfilter (z. B. "Heute", "Gestern", "Letzte Woche" etc.)

    Returns:
        Aggregierter DataFrame mit gruppierten Zeitwerten.
    """
    # Sicherstellen, dass Timestamps korrekt interpretiert werden
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        format="%Y-%m-%dT%H:%M:%S.%f",
        errors="coerce"
    )

    # Dynamisch runden je nach Filter
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
        df["rounded_time"] = df["timestamp"]  # Fallback ohne Runden

    # Aggregation auf die gerundete Zeit
    df = df.groupby("rounded_time").agg({
        "in_count": "max",
        "out_count": "max",
        "current_count": "max",
        "total_tracks": "max"
    }).reset_index()

    # Spalte zurück zu "timestamp" umbenennen
    df.rename(columns={"rounded_time": "timestamp"}, inplace=True)

    # Für Visualisierung (saubere Achsenbeschriftung)
    df["current_count"] = df["current_count"].round().astype(int)

    return df

# ────────────────────────────────────────────────────────────────────────────────
# 📊 Dashboard – Live-Zähler & Visualisierungen
# ────────────────────────────────────────────────────────────────────────────────
def show_live_counts() -> None:
    """
    Zeigt die aktuellen Live-Zähler im Dashboard an (IN, OUT, Aktuell, Tracks).

    Lädt die Daten aus der counter.json-Datei und zeigt sie in vier Spalten.
    """
    if not os.path.exists(COUNTER_PATH):
        st.warning("❌ Zählerdatei nicht gefunden.")
        return

    try:
        with open(COUNTER_PATH, "r") as f:
            data = json.load(f)

        # Live-Zähler anzeigen
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 IN", data.get("in", 0))
        col2.metric("🚪 OUT", data.get("out", 0))
        col3.metric("🟢 Aktuell", data.get("current", 0))
        col4.metric("🧠 Tracks", data.get("total_tracks", 0))

        # Zeitstempel anzeigen
        timestamp = data.get("timestamp")
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp)
                st.caption(f"Aktualisiert: {ts.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception:
                st.caption("⚠️ Ungültiger Zeitstempel")
        else:
            st.caption("ℹ️ Kein Zeitstempel verfügbar")

    except Exception as e:
        st.error(f"Fehler beim Laden der Zähldaten: {e}")


def show_count_history(df: pd.DataFrame, time_filter: str, y_axis_step: int = 1) -> None:
    """
    Zeigt den Verlauf der Personenzahl im Raum als Liniendiagramm.

    Args:
        df (pd.DataFrame): Aggregierte Zähldaten.
        time_filter (str): Zeitintervall wie "Heute", "Gestern", etc.
        y_axis_step (int): Optionaler Schritt für die y-Achse.
    """
    # Format & Ticks je nach Zeitraum
    format_map = {
        "Heute": ("%H:%M", "hour"),
        "Gestern": ("%H:%M", "hour"),
        "Letzte Woche": ("%d.%m.", "day"),
        "Letzter Monat": ("%d.%m.", "day"),
        "Letztes Jahr": ("%b %Y", "month"),
        "Insgesamt": ("%b %Y", "month")
    }
    x_format, tick_count = format_map.get(time_filter, ("%d.%m.", "day"))

    # Leere Daten prüfen
    if df.empty:
        st.info("ℹ️ Keine Daten für den ausgewählten Zeitraum.")
        return

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.sort_values("timestamp")
    df["current_count"] = df["current_count"].fillna(0).astype(int)

    x_axis = alt.X(
        "timestamp:T",
        title="Zeit",
        axis=alt.Axis(format=x_format, tickCount=tick_count, labelAngle=0)
    )

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


def show_hourly_distribution(df: pd.DataFrame) -> alt.Chart:
    """
    Erstellt ein Balkendiagramm mit der Verteilung der erfassten Personen pro Stunde.

    Args:
        df (pd.DataFrame): Zeitstempelbasierter Zähldatensatz mit Spalte 'in_delta'.

    Returns:
        alt.Chart: Altair-Balkendiagramm mit Personenverteilung nach Stunde.
    """
    if df.empty or "timestamp" not in df.columns or "in_delta" not in df.columns:
        return alt.Chart(pd.DataFrame(columns=["hour", "in_delta"])).mark_bar().encode(
            x=alt.X("hour:O", title="Stunde des Tages"),
            y=alt.Y("in_delta:Q", title="Personenanzahl")
        ).properties(
            width="container",
            height=300,
            title="📊 Personen pro Stunde (keine Daten)"
        )

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
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


def show_daily_average(df: pd.DataFrame) -> alt.Chart:
    """
    Zeigt den durchschnittlichen Tagesverlauf der Personenzählung.

    Args:
        df (pd.DataFrame): Zeitstempelbasierter Zähldatensatz mit Spalte 'in_delta'.

    Returns:
        alt.Chart: Altair-Liniendiagramm mit Durchschnittszählung pro Zeitfenster.
    """
    if df.empty or "timestamp" not in df.columns:
        return alt.Chart(pd.DataFrame(columns=["time", "in_delta"])).mark_line().encode(
            x="time:O", y="in_delta:Q"
        ).properties(
            height=300,
            title="📈 Durchschnittlicher Tagesverlauf (keine Daten)"
        )

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Fehlende Spalte dynamisch berechnen
    if "in_delta" not in df.columns and "in_count" in df.columns:
        df["in_delta"] = df["in_count"].diff().fillna(df["in_count"]).clip(lower=0)
    elif "in_delta" not in df.columns:
        df["in_delta"] = 0

    # Zeit extrahieren (nur Uhrzeit für Gruppierung)
    df["time"] = df["timestamp"].dt.strftime("%H:%M")
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
# 🧭 Konfigurationsmodus – Schrittweises UI (Schritt 1–4 + Übersicht)
# ────────────────────────────────────────────────────────────────────────────────
def draw_instruction_step(step: int) -> None:
    """
    Zeigt eine kontextabhängige Info-Beschreibung für den aktuellen Konfigurationsschritt an.

    Args:
        step (int): Schrittzahl im Konfigurationsprozess (1–4).
    """
    titles = {
        1: "📷 Bild aufnehmen",
        2: "🟦 Zählbereich definieren",
        3: "➡️ Eintrittsrichtung definieren",
        4: "💾 Konfiguration bestätigen"
    }

    messages = {
        1: "📷 Bitte ein Bild aufnehmen und danach auf 'Weiter' klicken." if os.path.exists(IMAGE_PATH)
           else "📷 Bitte ein neues Bild aufnehmen.",
        2: "🟦 Markiere den Zählbereich in Form eines Rechtecks.",
        3: "➡️ Wähle, aus welcher Richtung Personen den Raum **betreten**.",
        4: "💾 Überprüfe und speichere die Konfiguration."
    }

    st.markdown(f"## 🧭 Konfiguration: Schritt {step} – {titles.get(step, 'Unbekannt')}")
    st.info(messages.get(step, "Unbekannter Schritt."))

def draw_capture_ui_step() -> None:
    """
    Konfigurations-Schritt 1: Kamera auslösen und aufgenommenes Bild anzeigen.
    """
    st.subheader("📷 Schritt 1: Bild aufnehmen")

    if st.button("📷 Bild aufnehmen"):
        with st.spinner("Kamera wird aktiviert..."):
            try:
                success = capture_image()
                if success:
                    st.session_state.image_updated = True
                    st.success("Bild erfolgreich aufgenommen.")
                else:
                    st.error("❌ Aufnahme fehlgeschlagen.")
            except Exception as e:
                st.error(f"Fehler bei der Kameraaufnahme: {e}")

    if st.session_state.get("image_updated") or os.path.exists(IMAGE_PATH):
        try:
            img = load_image_fresh(IMAGE_PATH)
            st.image(img, caption="📸 Aufgenommenes Bild", width=1280)
        except Exception as e:
            st.error(f"Bild konnte nicht geladen werden: {e}")

    if os.path.exists(IMAGE_PATH) and st.button("➡ Weiter zu Schritt 2"):
        st.session_state.step = 2
        st.session_state.image_updated = False
        st.rerun()


def draw_bbox_ui_step() -> None:
    """
    Ermöglicht das Einzeichnen einer Zähl-Bounding-Box auf dem aufgenommenen Kamerabild.
    Übergang zu Schritt 3 erfolgt bei Bestätigung.
    """
    if not os.path.exists(IMAGE_PATH):
        st.warning("❌ Kein Bild gefunden. Bitte zuerst ein Bild aufnehmen (Schritt 1).")
        return

    try:
        image = load_image_fresh(IMAGE_PATH)
    except Exception as e:
        st.error(f"Fehler beim Laden des Bildes: {e}")
        return

    canvas = st_canvas(
        fill_color="rgba(0, 123, 255, 0.3)",
        stroke_width=3,
        stroke_color="#007BFF",
        background_image=image,
        update_streamlit=True,
        height=720,
        width=1280,
        drawing_mode="rect",
        key="bbox_step"
    )

    # Bounding Box extrahieren
    objects = canvas.json_data.get("objects") if canvas.json_data else None
    if objects:
        obj = objects[-1]
        bbox = {
            "x": int(obj["left"]),
            "y": int(obj["top"]),
            "w": int(obj["width"]),
            "h": int(obj["height"])
        }
        if st.button("➡ Weiter zu Schritt 3"):
            save_bbox(bbox)
            st.session_state.bbox = bbox
            st.session_state.step = 3
            st.rerun()

    # Erfolgsmeldung bei vorhandener Box (auch nach Neustart)
    if load_bbox():
        st.success("✅ Zählbereich wurde erfolgreich gespeichert.")


def draw_direction_ui_step() -> None:
    """
    Schritt 3 der Konfiguration: Eintrittsrichtung wählen – links/rechts.
    Die Buttons stehen links/rechts oberhalb des Bildes.
    """
    st.markdown("### ➡️ Eintrittsrichtung definieren")

    # Responsive Spalten über die Bildbreite verteilen
    col1, col2, col3 = st.columns([1, 6, 1])  # 1:6:1 Verhältnis → Buttons außen

    with col1:
        if st.button("➡️ Eintritt von links nach rechts"):
            st.session_state.direction = {"entry": "left_to_right", "angle": 0}
            st.session_state.step = 4
            st.rerun()

    with col3:
        if st.button("⬅️ Eintritt von rechts nach links"):
            st.session_state.direction = {"entry": "right_to_left", "angle": 180}
            st.session_state.step = 4
            st.rerun()

    # Vorschau des eingezeichneten Bereichs zentriert
    draw_bbox_preview_only()


def draw_bbox_preview_only() -> None:
    """
    Zeigt eine Vorschau des aktuell gespeicherten Zählbereichs (Bounding Box)
    auf dem aufgenommenen Bild. Wird z. B. nach Schritt 2 oder bei Richtungsauswahl verwendet.
    """
    if not os.path.exists(IMAGE_PATH):
        st.warning("⚠️ Kein Bild gefunden.")
        return

    bbox = st.session_state.get("bbox")
    if not bbox:
        st.warning("⚠️ Kein Zählbereich definiert.")
        return

    try:
        img = load_image_fresh(IMAGE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)

        draw.rectangle(
            [(bbox["x"], bbox["y"]), (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"])],
            outline="blue", width=4
        )
        st.image(img, caption="Zählbereich-Vorschau", width=1280)

    except Exception as e:
        st.error(f"Fehler beim Zeichnen der Vorschau: {e}")


def draw_overview_and_save() -> None:
    """
    Zeigt eine finale Vorschau der Konfiguration (Bounding Box + Richtungspfeil),
    erlaubt Speicherung oder Abbruch der Konfiguration.
    """
    if not os.path.exists(IMAGE_PATH):
        st.warning("❌ Kein Bild gefunden.")
        return

    bbox = st.session_state.get("bbox")
    direction = st.session_state.get("direction")

    if not bbox or not direction:
        st.error("❌ Bounding Box oder Richtung fehlt.")
        return

    try:
        # ─ Bild laden und zeichnen ─
        img = load_image_fresh(IMAGE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)

        draw.rectangle(
            [(bbox["x"], bbox["y"]), (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"])],
            outline="blue", width=4
        )

        entry = direction["entry"]
        p1, p2 = ((100, 360), (1180, 360)) if entry == "left_to_right" else ((1180, 360), (100, 360))
        draw.line([p1, p2], fill="red", width=5)
        draw_arrowhead(draw, p1, p2)
        draw.ellipse((p1[0]-10, p1[1]-10, p1[0]+10, p1[1]+10), fill="green")

        de_label = "von links nach rechts" if entry == "left_to_right" else "von rechts nach links"
        st.success(f"{'➡️' if entry == 'left_to_right' else '⬅️'} Eintrittsrichtung: {de_label}")
        st.image(img, caption="Vorschau: Zählbereich + Richtungspfeil", width=1280)

        # ─ Richtung speichern ─
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        angle = math.degrees(math.atan2(dy, dx))

        if st.button("💾 Konfiguration speichern & System starten"):
            with open(DIRECTION_PATH, "w") as f:
                json.dump(st.session_state.direction, f, indent=4)
            with open("camera.lock", "w") as f:
                f.write("counting")

            st.session_state.pop("step", None)
            st.success("✅ Konfiguration gespeichert. System startet...")
            st.rerun()

        if st.button("❌ Abbrechen & Neue Konfiguration starten"):
            reset_config(delete_files=True)
            st.rerun()

    except Exception as e:
        st.error(f"Fehler beim Zeichnen/Speichern: {e}")



def reset_config(delete_files: bool = False) -> None:
    """Hilfsfunktion zum Rücksetzen des Konfigurationszustands."""
    st.session_state.step = 1
    st.session_state.bbox = None
    st.session_state.direction = []
    if delete_files:
        for path in [CONFIG_PATH, DIRECTION_PATH, LOCK_PATH]:
            if os.path.exists(path):
                os.remove(path)


def show_config_overview() -> None:
    """
    Zeigt eine Übersicht der aktuellen Konfiguration inklusive Bild, Zählbereich
    und Eintrittsrichtung. Bietet Möglichkeit zur Neuerstellung.
    """
    st.markdown("## 🧭 Konfiguration")

    bbox = load_bbox()
    if not bbox or not os.path.exists(DIRECTION_PATH):
        st.info("ℹ️ Noch keine vollständige Konfiguration vorhanden.")
        return

    try:
        # Bild vorbereiten
        img = load_image_fresh(IMAGE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Bounding Box zeichnen
        draw.rectangle(
            [(bbox["x"], bbox["y"]), (bbox["x"] + bbox["w"], bbox["y"] + bbox["h"])],
            outline="blue", width=4
        )

        # Eintrittsrichtung laden und darstellen
        with open(DIRECTION_PATH, "r") as f:
            direction = json.load(f)

        entry = direction["entry"]
        p1, p2 = ((100, 360), (1180, 360)) if entry == "left_to_right" else ((1180, 360), (100, 360))
        draw.line([p1, p2], fill="red", width=5)
        draw_arrowhead(draw, p1, p2)
        draw.ellipse((p1[0]-10, p1[1]-10, p1[0]+10, p1[1]+10), fill="green")

        # Bild anzeigen
        st.image(img, caption="Aktuelle Konfiguration", width=1280)

    except Exception as e:
        st.error(f"Fehler beim Laden der Übersicht: {e}")
        return

    if st.button("🔁 Neue Konfiguration starten"):
        reset_config(delete_files=True)
        st.rerun()
