FROM python:3.13.17-slim-trixie AS base

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /usr/local/bin/uv
RUN python3 -m pip uninstall --yes pip
RUN apt-get update \
  && apt-get install -y --no-install-recommends git \
  && rm -rf /var/lib/apt/lists/*

CMD ["./bin/run_server_locally"]
