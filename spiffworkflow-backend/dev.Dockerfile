FROM python:3.12.1-slim-bookworm

WORKDIR /app

RUN apt-get update \
  && apt-get install -y -q \
  gcc libssl-dev libpq-dev default-libmysqlclient-dev \
  pkg-config libffi-dev git-core curl sqlite3 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install poetry==1.8.1 pytest-xdist==3.5.0

CMD ["./bin/run_server_locally"]
