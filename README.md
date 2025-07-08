# EKSPAR – Kamera-basiertes Personenzählsystem

## 📌 Projektziel

EKSPAR ist ein datenschutzkonformes, modular aufgebautes System zur anonymen Personenzählung in Räumen mit Hilfe einer AI-Kamera und Echtzeit-Tracking.

## 🔧 Systemstruktur

- Kamera (Picamera2)
- YOLOv8 Inferenz
- Objekterkennung und Tracking
- IN/OUT-Zählung via Zähllinie
- Logging in SQLite-Datenbank
- Visualisierung via Streamlit Dashboard

## 📁 Projektstruktur

Siehe `backend/`, `frontend/`, `models/`, `scripts/`, `data/` usw.

## 🚀 Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run frontend/dashboard.py


## Befehle zum start
source .venv/bin/activate

## Dashboard
streamlit run frontend/dashboard.py

## Kamera
python backend/camera/camera_capture.py

## Zählsystem
python backend/detection/PersonCounter.py


rpicam-hello -t 0 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json

## 📊 Dashboard-Analysefunktionen

![EKSPAR Dashboard Vorschau](static/dashboard_preview.png)


| Funktion                                   | Beschreibung                                                                |
|-------------------------------------------|-----------------------------------------------------------------------------|
| 👥 Live-Zähler                             | Anzeige von IN, OUT, Personen im Raum, aktive Tracks                        |
| 📈 Zeitverlauf                             | Verlauf der Personenanzahl im Raum über gewählten Zeitraum                  |
| 📊 Personen pro Stunde                     | Balkendiagramm der IN-Zugänge pro Stunde (für Heute, Gestern, Letzte Woche) |
| 📉 Durchschnittlicher Tagesverlauf         | Gemittelte IN-Werte pro Uhrzeit (z. B. 08:00, 09:00…) für längerfristige Zeiträume |
| 📤 CSV-Export                              | Export der aggregierten Zeitreihendaten im CSV-Format                       |
| 🟦 Konfigurationsmodus                     | Markierung des Türbereichs für Zählung über das Bild                        |
