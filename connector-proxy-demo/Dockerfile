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
 && apt-get install -y -q git-core curl procps gunicorn3 default-mysql-client vim-tiny \
 && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.6.1


######################## - SETUP

# Setup image for installing Python dependencies.
FROM base AS setup

# poetry 1.4 seems to cause an issue where it errors with
#   This error originates from the build backend, and is likely not a
#   problem with poetry but with lazy-object-proxy (1.7.1) not supporting PEP 517 builds.
#   You can verify this by running 'pip wheel --use-pep517 "lazy-object-proxy (==1.7.1) ; python_version >= "3.6""'.
# Pinnning to 1.3.2 to attempt to avoid it.
RUN pip install poetry==1.6.1
RUN useradd _gunicorn --no-create-home --user-group

RUN apt-get update \
 && apt-get install -y -q gcc libssl-dev pkg-config

# poetry install takes a long time and can be cached if dependencies don't change,
# so that's why we tolerate running it twice.
COPY pyproject.toml poetry.lock /app/
RUN poetry install

COPY . /app
RUN poetry install


######################## - FINAL

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena/connector-proxy-demo"
LABEL description="Demo connector proxy component for SpiffWorkflow"

COPY --from=setup /app /app

CMD ["./bin/boot_server_in_docker"]
