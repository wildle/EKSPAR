import streamlit as st
import os
from backend.camera_interface import capture_image
from frontend.components import draw_bbox_ui  # Bounding Box UI importieren

IMAGE_PATH = "static/last_config.jpg"

# Layout-Setup
st.set_page_config(page_title="EKSPAR – Konfiguration", layout="wide")
st.title("📷 EKSPAR – Konfigurationsmodus")

st.markdown("### Schritt 1: Einzelbild aufnehmen")

# Button: Neues Bild aufnehmen
if st.button("📷 Neues Bild aufnehmen"):
    with st.spinner("Kamera aktiviert..."):
        success = capture_image()
    if success:
        st.success("Bild erfolgreich aufgenommen!")
    else:
        st.error("Fehler beim Aufnehmen des Bildes.")

# Bild anzeigen (zentriert)
if os.path.exists(IMAGE_PATH):
    st.markdown("##### Aufgenommenes Bild (1280×720)")
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.image(IMAGE_PATH, use_column_width=False, width=1280)

    # Schritt 2: Bounding Box zeichnen und speichern
    draw_bbox_ui()
else:
    st.warning("Noch kein Bild aufgenommen. Bitte zuerst ein Bild erstellen.")
