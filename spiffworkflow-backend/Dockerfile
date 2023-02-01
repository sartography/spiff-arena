# Base image to share ENV vars that activate VENV.
FROM ghcr.io/sartography/python:3.11 AS base

ENV VIRTUAL_ENV=/app/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# base plus packages needed for deployment. Could just install these in final, but then we can't cache as much.
FROM base AS deployment

RUN apt-get update \
 && apt-get clean -y \
 && apt-get install -y -q curl git-core gunicorn3 default-mysql-client \
 && rm -rf /var/lib/apt/lists/*

# Setup image for installing Python dependencies.
FROM base AS setup

RUN pip install poetry
RUN useradd _gunicorn --no-create-home --user-group

RUN apt-get update \
 && apt-get install -y -q gcc libssl-dev libpq-dev

# poetry install takes a long time and can be cached if dependencies don't change,
# so that's why we tolerate running it twice.
COPY pyproject.toml poetry.lock /app/
RUN poetry install --without dev

COPY . /app
RUN poetry install --without dev

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena"
LABEL description="Software development platform for building, running, and monitoring executable diagrams"

COPY --from=setup /app /app

CMD ["./bin/boot_server_in_docker"]
