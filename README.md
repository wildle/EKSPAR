# E.K.S.P.A.R.

**Entwicklung eines Kamera-basierten Systems zur Personenzählung und Analyse der Raumnutzung**

---

## 🔍 Projektbeschreibung

E.K.S.P.A.R. ist ein kamerabasiertes System, das mithilfe von KI-basierter Objekterkennung und einer interaktiven Weboberfläche die Bewegung von Personen in Räumen erfasst. Es ermöglicht die Konfiguration von Zähllinien über das Netzwerk und erfasst anonymisierte Zähldaten zur weiteren Analyse (z. B. in Wartebereichen).

---

## ⚙️ Systemanforderungen

- Raspberry Pi 4B (empfohlen: 4 GB RAM)
- Raspberry Pi Kamera Modul 3 (MIPI CSI-2)
- Raspberry Pi OS (Bookworm empfohlen)
- Python 3.11+
- Internetverbindung (für erste Installation)
- Lokales Netzwerk (für Webzugriff vom Praxispersonal)

---

## 📦 Installation

```bash
# 1. Projekt klonen
git clone https://github.com/<dein-repo>/EKSPAR.git
cd EKSPAR

# 2. Python-Umgebung vorbereiten
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Systempakete (nur einmalig)
sudo apt update
sudo apt install python3-picamera2 libcamera-dev

cd backend
FLASK_APP=app.py flask run --host=0.0.0.0 --port=5050

http://<Raspberry-IP>:5050/config
