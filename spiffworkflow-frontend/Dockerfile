# Base image to share ENV vars that activate VENV.
FROM node:24.18.0-trixie-slim@sha256:ae91dcc111a68c9d2d81ff2a17bda61be126426176fde6fe7d08ab13b7f50573 AS base

RUN mkdir /app

WORKDIR /app

# curl for debugging
# procps for debugging
# vim ftw
RUN apt-get update \
  && apt-get clean -y \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y -q \
  curl \
  procps \
  vim-tiny \
  libkrb5support0 \
  libexpat1 \
  && rm -rf /var/lib/apt/lists/*

# this matches total memory on spiffworkflow-demo
ENV NODE_OPTIONS=--max_old_space_size=4096


######################## - SETUP
# Setup image for installing JS dependencies.
FROM base AS setup

COPY package.json package-lock.json .npmrc /app/

# npm ci because it respects the lock file.
# --ignore-scripts because authors can do bad things in postinstall scripts.
# https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html
# npx can-i-ignore-scripts can check that it's safe to ignore scripts.
RUN npm ci --ignore-scripts

COPY . /app/
RUN ./bin/build


######################## - FINAL

# Use nginx as the base image
# FROM nginx:1.29.1-bookworm
FROM nginx:1.31-alpine@sha256:4a73073bd557c65b759505da037898b61f1be6cbcc3c2c3aeac22d2a470c1752

# we sort of love bash too much to use sh
RUN apk add --no-cache bash

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/*

# Copy the nginx configuration file
COPY docker_build/nginx.conf.template /var/tmp

# Copy the built static files into the nginx directory
COPY --from=setup /app/dist /usr/share/nginx/html
COPY --from=setup /app/bin /app/bin

CMD ["/app/bin/boot_server_in_docker"]
