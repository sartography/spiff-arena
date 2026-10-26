# Base image to share ENV vars that activate VENV.
FROM python:3.13.17-slim-trixie AS base

ENV VIRTUAL_ENV=/app/.venv
RUN python3 -m venv --without-pip $VIRTUAL_ENV \
  && python3 -m pip uninstall --yes pip
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app


######################## - DEPLOYMENT

# base plus packages needed for deployment. Could just install these in final, but then we can't cache as much.
# vim is just for debugging
FROM base AS deployment

# git-core because the app does "git commit", etc
# curl because the docker health check uses it
# procps because it is useful for debugging
# gunicorn3 for web server
# default-mysql-client for convenience accessing mysql docker container
# vim ftw
RUN apt-get update \
  && apt-get clean -y \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -q git-core curl procps gunicorn3 default-mysql-client vim-tiny libkrb5support0 libexpat1 \
  && rm -rf /var/lib/apt/lists/*


######################## - SETUP

# Setup image for installing Python dependencies.
FROM base AS setup

COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /usr/local/bin/uv
RUN useradd _gunicorn --no-create-home --user-group

RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -q gcc git libssl-dev pkg-config

COPY . /app
RUN uv sync --locked --no-dev


######################## - FINAL

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena/connector-proxy-demo"
LABEL description="Demo connector proxy component for SpiffWorkflow"

COPY --from=setup /app /app

CMD ["./bin/boot_server_in_docker"]
