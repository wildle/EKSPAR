FROM python:3.12.9-slim

WORKDIR /app

COPY ./opencv /app

# Install system dependencies for OpenCV
RUN apt update && apt install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

# Install OpenCV dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Keep the container alive
CMD ["bash", "-c", "while true; do sleep 1000; done"]
