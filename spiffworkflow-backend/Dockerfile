# Base image to share ENV vars that activate VENV.

# References
# https://oandersonbm.medium.com/python-docker-image-security-and-trivy-scan-e8c90a2ffe28
# https://docs.astral.sh/uv/guides/integration/docker/#installing-a-project
# https://codegym.cc/groups/posts/python-docker-for-beginners

FROM python:3.13-alpine AS base

ENV UV_NO_SYNC=true
ENV VIRTUAL_ENV=/app/.venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# set timezone to UTC
RUN cp /usr/share/zoneinfo/UTC /etc/localtime && echo "UTC" > /etc/timezone

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
# libpq in order to be able to use postgres at runtime
# mariadb-connector-c provides libmariadb and its authentication plugins at runtime
# bash is needed from backend

RUN apk update \
 && apk add --no-cache git curl procps mysql-client mariadb-connector-c vim jq libpq krb5-libs libexpat bash \
 && rm -rf /var/cache/apk/*

# keep pip up to date
RUN pip install --upgrade pip

# use ghcr.io/astral-sh/uv and provide it in FINAL with copy from /usr/local

# Avoid host:container file ownership issues
RUN git config --global --add safe.directory '*'

######################## - SETUP

# Setup image for installing Python dependencies.
FROM base AS setup

# Astral is the company behind uv
COPY --from=ghcr.io/astral-sh/uv:alpine /usr/local/bin/uv /usr/local/bin/uvx /usr/local/bin/

# mysqldev for mysqlclient lib
# libpq-dev in order to be able to install postgres lib. See also libpq above in deployment image.
# libc-dev is for uv build psycopg2
# curl-dev is for uv build pcurl
RUN apk add --no-cache gcc git openssl-dev libpq-dev mysql-dev pkgconfig libffi-dev libc-dev curl-dev

COPY . /app
RUN uv sync --no-dev --frozen

######################## - FINAL

# Final image without setup dependencies.
FROM deployment AS final

LABEL source="https://github.com/sartography/spiff-arena/spiffworkflow-backend"
LABEL description="Backend component of SpiffWorkflow, a software development platform for building, running, and monitoring executable diagrams"

# container log warning: Using `httpx` with `starlette.testclient` is deprecated => sporadically with alpine AND debian trixie

# copy alpine dir /usr/local with uv included
COPY --from=setup /usr/local /usr

# copy /app with /app/.venv included
COPY --from=setup /app /app

CMD ["./bin/boot_server_in_docker"]
