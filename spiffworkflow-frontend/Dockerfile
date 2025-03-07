# Base image to share ENV vars that activate VENV.
FROM node:22.3.0-bookworm-slim AS base

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
ENV NODE_OPTIONS=--max_old_space_size=2048


######################## - SETUP

# Setup image for installing JS dependencies.
FROM base AS setup

COPY . /app/

# npm ci because it respects the lock file.
# --ignore-scripts because authors can do bad things in postinstall scripts.
# https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html
# npx can-i-ignore-scripts can check that it's safe to ignore scripts.
RUN npm ci --ignore-scripts

RUN ./bin/build


######################## - FINAL

# Use nginx as the base image
FROM nginx:1.25.4-bookworm

RUN apt-get update \
  && apt-get clean -y \
  && apt-get install -y -q \
  libkrb5support0 \
  libexpat1 \
  libaom3 \
  && rm -rf /var/lib/apt/lists/*

# Remove default nginx configuration
RUN rm -rf /etc/nginx/conf.d/*

# Copy the nginx configuration file
COPY docker_build/nginx.conf.template /var/tmp

# Copy the built static files into the nginx directory
COPY --from=setup /app/dist /usr/share/nginx/html
COPY --from=setup /app/bin /app/bin

CMD ["/app/bin/boot_server_in_docker"]
