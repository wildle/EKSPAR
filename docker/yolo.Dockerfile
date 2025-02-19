FROM python:3.12.9-slim

WORKDIR /app

COPY ./yolo /app

# Install system dependencies
RUN apt update && apt install -y libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir flask ultralytics

# Expose the correct port
EXPOSE 5002

# Start Flask inside YOLO container
CMD ["python", "/app/yolo_main.py"]
