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
