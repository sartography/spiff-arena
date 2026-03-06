# Base image to share ENV vars that activate VENV.
FROM node:24.13.0-trixie-slim AS base

RUN mkdir /app

WORKDIR /app

# curl for debugging
# procps for debugging
# vim ftw
RUN apt-get update \
  && apt-get clean -y \
  && apt-get install -y -q \
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

COPY package.json package-lock.json /app/

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
FROM nginx:1.29.5-alpine

# we sort of love bash too much to use sh
RUN apk add --no-cache bash

# to fix security vulnerability:
# remove this line once the base image has the secure version of this lib (10.46)
RUN apk add --upgrade pcre2

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/*

# Copy the nginx configuration file
COPY docker_build/nginx.conf.template /var/tmp

# Copy the built static files into the nginx directory
COPY --from=setup /app/dist /usr/share/nginx/html
COPY --from=setup /app/bin /app/bin

CMD ["/app/bin/boot_server_in_docker"]
