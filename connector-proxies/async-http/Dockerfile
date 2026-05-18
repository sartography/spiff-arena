FROM python:3.13.13-slim-trixie

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY bin ./bin

CMD ["./bin/boot_server_in_docker"]
