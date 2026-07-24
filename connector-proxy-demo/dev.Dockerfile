FROM python:3.14.6-slim-trixie@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS base

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry==2.4.1 pytest-xdist==3.5.0

CMD ["./bin/run_server_locally"]
