#!/bin/bash

# ──────────────────────────────────────────────────────────────
# EKSPAR – Startskript für Kamera, Dashboard & Live-Zählung
# Entwickelt für Raspberry Pi
# Autor: [Dein Name]
# ──────────────────────────────────────────────────────────────

# Absoluter Pfad zur Projektbasis
BASE_DIR="/home/jarvis/EKSPAR"
VENV="$BASE_DIR/.venv"

# ──────────────────────────────────────────────────────────────
# 1. Kameraaufnahme starten (außerhalb der venv)
echo "[INFO] Starte Kameraaufnahme (camera_capture.py)..."
/usr/bin/python3 "$BASE_DIR/src/backend/camera/camera_capture.py" &
CAMERA_PID=$!
sleep 1

# ──────────────────────────────────────────────────────────────
# 2. Streamlit Dashboard starten (innerhalb der venv)
echo "[INFO] Starte Streamlit-Dashboard (dashboard.py)..."
source "$VENV/bin/activate"
PYTHONPATH="$BASE_DIR/src" streamlit run "$BASE_DIR/src/frontend/dashboard.py" &
DASHBOARD_PID=$!
sleep 1

# ──────────────────────────────────────────────────────────────
# 3. Objektzählung starten (innerhalb der venv)
echo "[INFO] Starte Objektzählung (ObjectCounting.py)..."
python3 "$BASE_DIR/src/counter/ObjectCounting.py" &
COUNTING_PID=$!

# ──────────────────────────────────────────────────────────────
# Prozesse laufen lassen – beende mit CTRL+C
trap "echo ''; echo '[INFO] Stoppe Prozesse...'; kill $CAMERA_PID $DASHBOARD_PID $COUNTING_PID; exit" SIGINT

wait
