# Verwende das offizielle Python-Image als Basis
FROM python:3.10-slim

# Setze das Arbeitsverzeichnis in den Container
WORKDIR /app

# Kopiere den aktuellen Verzeichnisinhalt in den Container
COPY . /app

# Installiere Flask und OpenCV in den Container
RUN pip install Flask opencv-python-headless

# Stelle sicher, dass Port 5000 für den Zugriff von außen freigegeben wird
EXPOSE 5000

# Starte die Flask-App
CMD ["python", "app.py"]
