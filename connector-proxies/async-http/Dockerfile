FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD [ "granian", "--host", "0.0.0.0", "--port", "8080", "--interface", "asgi", "main:app" ]
