FROM python:3.13.13-slim-trixie AS base

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry==2.4.1 pytest-xdist==3.5.0

CMD ["./bin/run_server_locally"]
