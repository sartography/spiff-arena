FROM python:3.12-slim AS base

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry==1.8.1 pytest-xdist==3.5.0

CMD ["./bin/run_server_locally"]
