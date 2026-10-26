FROM python:3.13.13-alpine

WORKDIR /app

COPY requirements.txt .

# ca-certificates is upgraded because the pinned base image still trusts the distrusted eMudhra emSign G3 roots
RUN apk upgrade --no-cache ca-certificates ca-certificates-bundle \
  && apk add --no-cache bash \
  && pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY bin ./bin

CMD ["./bin/boot_server_in_docker"]
