FROM python:3.12.1-slim-bookworm

WORKDIR /app

RUN apt-get update \
  && apt-get install -y -q \
  curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY elasticsearch.py elasticsearch.py

CMD ["python", "elasticsearch.py"]
