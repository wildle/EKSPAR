# Basis-Image mit Python 3.11
FROM python:3.11

# Arbeitsverzeichnis setzen
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY . .

# Flask-Server starten
CMD ["python", "app.py"]
