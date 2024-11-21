# Base image to share ENV vars that activate VENV.
FROM python:3.12.1-slim-bookworm AS base

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
# jq because it is really useful, even for scenarios where people might have environment variables with json values they might need to use for configs. about 1MB.
RUN apt-get update \
  && apt-get install -y -q libaio1 \
  && apt-get install -y -q git-core curl procps gunicorn3 default-mysql-client vim-tiny jq \
  && rm -rf /var/lib/apt/lists/*

# keep pip up to date
RUN pip install --upgrade pip
RUN pip install poetry==1.8.1 hdbcli oracledb nfelib

RUN apt-get update && apt-get install -y libpq5

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

# default-libmysqlclient-dev for mysqlclient lib
RUN apt-get update \
 && apt-get install -y -q gcc libssl-dev libpq-dev default-libmysqlclient-dev pkg-config libffi-dev dos2unix git nano curl unzip

RUN pip install hdbcli pandas openpyxl postgres aes-everywhere pybase64 jinja2
 
# poetry install takes a long time and can be cached if dependencies don't change,
# so that's why we tolerate running it twice.
COPY pyproject.toml poetry.lock /app/

RUN poetry install --without dev

RUN git clone https://github.com/emersonlgregorio/connectordb.git

RUN mv connectordb /app/venv/lib/python3.12/site-packages/

# Update library path
ENV LD_LIBRARY_PATH="/app/oracle/instantclient_21_13:$LD_LIBRARY_PATH"

COPY . /app

RUN dos2unix /app/bin/boot_server_in_docker

RUN poetry install --without dev

######################## - FINAL

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena/spiffworkflow-backend"
LABEL description="Backend component of SpiffWorkflow, a software development platform for building, running, and monitoring executable diagrams"

COPY --from=setup /app /app

# Set library path in the final stage
ENV LD_LIBRARY_PATH="/app/oracle/instantclient_21_13:$LD_LIBRARY_PATH"

CMD ["./bin/boot_server_in_docker"]
