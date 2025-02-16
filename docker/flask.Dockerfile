FROM python:3.12.9-slim

WORKDIR /app

COPY ./flask-app /app

# Install system utilities (ping)
RUN apt update && apt install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# Install Flask dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "/app/app.py"]
