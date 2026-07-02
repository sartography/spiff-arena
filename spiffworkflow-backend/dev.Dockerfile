FROM python:3.14.6-slim-trixie@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y -q \
  gcc libssl-dev libpq-dev default-libmysqlclient-dev \
  pkg-config libffi-dev git-core curl sqlite3 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install uv==0.10.0 pytest-xdist==3.6.1

CMD ["./bin/run_server_locally"]
