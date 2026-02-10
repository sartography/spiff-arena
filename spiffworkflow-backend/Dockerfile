# Base image to share ENV vars that activate VENV.
FROM python:3.13.12-slim-trixie AS base

ENV UV_NO_SYNC=true
ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app


######################## - DEPLOYMENT

# base plus packages needed for deployment. Could just install these in final, but then we can't cache as much.
# vim is just for debugging
FROM base AS deployment

# git-core because the app does "git commit", etc
# curl because the docker health check uses it
# procps because it is useful for debugging
# uvicorn for web server
# default-mysql-client for convenience accessing mysql docker container
# vim ftw
# jq because it is really useful, even for scenarios where people might have environment variables with json values they might need to use for configs. about 1MB.
# libpq5 in order to be able to use postgres at runtime
RUN apt-get update \
  && apt-get clean -y \
  && apt-get install -y -q git-core curl procps default-mysql-client vim-tiny jq libpq5 libkrb5support0 libexpat1 \
  && rm -rf /var/lib/apt/lists/*

# keep pip up to date
RUN pip install --upgrade pip
RUN pip install uv==0.10.0

# Avoid host:container file ownership issues
RUN git config --global --add safe.directory '*'


######################## - SETUP

# Setup image for installing Python dependencies.
FROM base AS setup

RUN pip install uv==0.10.0

# default-libmysqlclient-dev for mysqlclient lib
# libpq-dev in order to be able to install postgres lib, psycopg2. See also libpq5 above in deployment image.
RUN apt-get update \
  && apt-get install -y -q gcc git libssl-dev libpq-dev default-libmysqlclient-dev pkg-config libffi-dev

COPY . /app
RUN uv sync --no-dev --frozen

######################## - FINAL

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena/spiffworkflow-backend"
LABEL description="Backend component of SpiffWorkflow, a software development platform for building, running, and monitoring executable diagrams"

COPY --from=setup /app /app
CMD ["./bin/boot_server_in_docker"]
