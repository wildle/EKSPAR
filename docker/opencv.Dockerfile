FROM python:3.12.9-slim

WORKDIR /app

COPY ./opencv /app

# Install system dependencies (inkl. curl für Debugging)
RUN apt update && apt install -y libgl1 libglib2.0-0 curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir flask opencv-python-headless

# Expose the correct port
EXPOSE 5001

# Start Flask inside OpenCV container
CMD ["python", "/app/opencv_main.py"]
