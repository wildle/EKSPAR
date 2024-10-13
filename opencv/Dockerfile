# Verwende das offizielle Python-Image als Basis
FROM python:3.10-slim

# Setze das Arbeitsverzeichnis in den Container
WORKDIR /app

# Installiere notwendige Abhängigkeiten für OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libgtk2.0-dev \
    && pip install opencv-python-headless

# Kopiere den aktuellen Verzeichnisinhalt in den Container
COPY . /app

# Standardmäßiger Befehl, um den Container aktiv zu halten (kann angepasst werden)
CMD ["tail", "-f", "/dev/null"]
