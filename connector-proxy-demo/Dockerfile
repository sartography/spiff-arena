# Base image to share ENV vars that activate VENV.
FROM python:3.11.6-slim-bookworm AS base

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
# gunicorn3 for web server
# default-mysql-client for convenience accessing mysql docker container
# vim ftw
RUN apt-get update \
 && apt-get clean -y \
 && apt-get install -y -q git-core curl procps gunicorn3 default-mysql-client vim-tiny dos2unix \
 && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.6.1


######################## - SETUP

# Setup image for installing Python dependencies.
FROM base AS setup

RUN pip install poetry==1.6.1
RUN useradd _gunicorn --no-create-home --user-group

RUN apt-get update \
  && apt-get install -y -q gcc libssl-dev pkg-config

RUN pip install postgres
# poetry install takes a long time and can be cached if dependencies don't change,
# so that's why we tolerate running it twice.
COPY pyproject.toml poetry.lock /app/

COPY . /app
RUN poetry install


######################## - FINAL

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena/connector-proxy-demo"
LABEL description="Demo connector proxy component for SpiffWorkflow"

COPY --from=setup /app /app

# Apply dos2unix to the boot script to remove Windows-style line endings
RUN dos2unix /app/bin/boot_server_in_docker

CMD ["./bin/boot_server_in_docker"]
