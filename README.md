# EKSPAR - Kamera-basiertes Personenzählsystem

Dieses Projekt implementiert ein Echtzeit-Personenzählsystem mit einer Raspberry Pi Kamera, YOLO11 zur Objekterkennung und einem Flask-basierten Dashboard zur Visualisierung.

## Installation & Setup
1. Klone das Repository:
git clone https://github.com/wildle/EKSPAR.git cd EKSPAR


2. Baue das Docker-Image und starte das Backend:
docker-compose build docker-compose up


3. Teste, ob das Backend läuft:
- **Öffne `http://localhost:5000/` in einem Browser**
- Sollte die Meldung **"Flask Backend läuft!"** zurückgeben
