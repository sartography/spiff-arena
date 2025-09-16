FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

CMD [ "granian", "--reload", "--host", "0.0.0.0", "--port", "8200", "--interface", "asgi", "main:app" ]
