FROM python:3.12.9-slim

WORKDIR /app

COPY ./opencv /app

# Install OpenCV dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "opencv_main.py"]
