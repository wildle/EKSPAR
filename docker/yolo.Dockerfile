FROM python:3.12.9-slim

WORKDIR /app

COPY ./yolo /app

# Install YOLO dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "yolo_main.py"]
