FROM python:3.12.9-slim

WORKDIR /app

COPY ./flask-app /app

# Install Flask dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "app.py"]
