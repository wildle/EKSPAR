import streamlit as st
import os
from backend.camera_interface import capture_image
from frontend.components import draw_bbox_ui  # <-- Bounding Box UI importieren

IMAGE_PATH = "static/last_config.jpg"

# Streamlit Layout
st.set_page_config(page_title="EKSPAR – Konfiguration", layout="centered")
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

# Bild anzeigen, falls vorhanden
if os.path.exists(IMAGE_PATH):
    st.image(IMAGE_PATH, caption="Aufgenommenes Bild", use_column_width=True)

    # Schritt 2: Bounding Box zeichnen und speichern
    draw_bbox_ui()
else:
    st.warning("Noch kein Bild aufgenommen. Bitte zuerst ein Bild erstellen.")
