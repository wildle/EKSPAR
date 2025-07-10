# EKSPAR – Kamera-basiertes Personenzählsystem

## 📌 Projektziel

**EKSPAR** (Edge-KI-System zur Personenanalyse in Räumen) ist ein datenschutzkonformes, modular aufgebautes Zählsystem mit Echtzeitverarbeitung auf dem Raspberry Pi 5. Es zählt anonym Personen, erkennt Eintrittsrichtungen und stellt die Ergebnisse über ein Dashboard zur Verfügung. Es werden **keine Bilder oder Videos gespeichert**.

## 🛠 Systemübersicht

* Raspberry Pi 5 + AI-Kamera (picamera2)
* Live-Objekterkennung mit YOLOv11n (Ultralytics)
* Zählung durch Eintritt in eine konfigurierbare Region (Bounding Box)
* Richtungsvorgabe per Winkelkonfiguration (`angle`)
* Metadatenspeicherung (JSON + SQLite)
* Visualisierung im Streamlit-Dashboard

## 📂 Projektstruktur

```
EKSPAR/
├── ekspar.py                    # Hauptstarter (Dashboard + Zählung)
├── backend/
│   ├── detection/person_counter.py
│   ├── config/bbox_config.json
│   ├── config/direction_config.json
│   └── camera/
│       ├── capture_raw.py       # Einzelbild für Konfiguration
│       └── camera_interface.py  # Subprozess-Ausführung für picamera2
├── frontend/
│   ├── dashboard.py             # Streamlit-Oberfläche
│   └── components.py            # UI-Komponenten
├── models/yolo11n.pt           # YOLOv11n-Modell
├── data/log.db                 # SQLite-Datenbank
├── data/counter.json           # Aktueller Zählstand
├── static/last_config.jpg      # Konfigurationsbild
├── requirements.txt            # Python-Abhängigkeiten
└── README.md                   # Diese Datei
```

## 🚀 Schnellstart

### 1. Umgebung vorbereiten

```bash
sudo apt update && sudo apt install python3-picamera2 -y  # Kamera-Support
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. System starten

```bash
python ekspar.py
```

Das Script erkennt automatisch, ob eine Konfiguration vorhanden ist, und startet:

* den **Zählmodus** oder
* den **Konfigurationsmodus** (falls keine Bounding Box definiert ist)

## 🔍 Konfigurationsmodus

1. Starte `ekspar.py` ohne vorhandene `bbox_config.json`
2. Im Dashboard:

   * Schritt 1: Neues Bild aufnehmen (Kamera)
   * Schritt 2: Zählbereich einzeichnen (Box)
   * Schritt 3: Eintrittsrichtung definieren (2 Pfeilpunkte)
   * Schritt 4: Übersicht überprüfen und Konfiguration speichern
3. Danach beginnt automatisch der Zählmodus

## 📊 Live-Zählung

* Die Kamera erfasst Personen im konfigurierten Bereich
* Die Bewegungsrichtung wird **nicht erkannt**, sondern anhand des konfigurierten Winkels umgedreht (z. B. `angle = 180` → IN/OUT getauscht)
* Die **aktuelle Anzahl**, **IN/OUT-Zahlen** und **Verlauf** werden:

  * in `data/counter.json` gespeichert
  * in `data/log.db` (SQLite) geloggt
  * im Dashboard visualisiert

## 🗓 Dashboard-Funktionen

| Funktion               | Beschreibung                                                             |
| ---------------------- | ------------------------------------------------------------------------ |
| 👥 Live-Zähler         | Echtzeit-Anzeige von IN, OUT, aktuelle Personenanzahl                    |
| 📈 Verlauf             | Aggregierte Zeitreihe der Personen im Raum                               |
| 🔹 Personen pro Stunde | Balkendiagramm der Eintritte ("Heute", "Gestern", "Letzte Woche")        |
| 🔷 Tagesverlauf (avg.) | Durchschnittlicher Tagesverlauf (z. B. 08:00, 09:00...) für mehrere Tage |
| 📄 CSV-Export          | Zeitreihendaten als CSV-Datei exportieren                                |
| 📷 Konfiguration       | Bildaufnahme, Bounding Box, Richtungspfeil                               |

## 🛠 Hinweise zur Kamera

* Die Aufnahme erfolgt über `picamera2` **außerhalb der virtuellen Umgebung**
* Dazu wird das Skript `capture_raw.py` via Subprozess aufgerufen
* Voraussetzung: Raspberry Pi OS mit `libcamera`

```bash
sudo apt install python3-picamera2
```

## 🔎 Technische Besonderheiten

* Kamera-Modussteuerung über `camera.lock` ("config" vs. "counting")
* Headless-Betrieb möglich (kein GUI erforderlich)
* Kein Cloud-Zugriff, volle Offline-Funktion

## 🧰 Entwicklungsabhängigkeiten

Siehe `requirements.txt`:

```
ultralytics==8.3.162
opencv-python==4.11.0.86
streamlit==1.44.1
streamlit-drawable-canvas==0.8.0
pillow==11.2.1
pandas==2.2.3
altair==5.5.0
```

---

> Entwickelt im Rahmen der Bachelorarbeit "Entwicklung eines Kamera-basierten
>
> Systems zur Personenzählung und Analyse der Raumnutzung" am MCI
