# Base image to share ENV vars that activate VENV.
FROM node:22.3.0-bookworm-slim AS base

RUN mkdir /app
WORKDIR /app

# Instala ferramentas úteis e dependências nativas
RUN apt-get update \
  && apt-get clean -y \
  && apt-get install -y -q \
  curl \
  procps \
  vim-tiny \
  libkrb5support0 \
  libexpat1 \
  && rm -rf /var/lib/apt/lists/*

ENV NODE_OPTIONS=--max_old_space_size=2048

######################## - SETUP

FROM base AS setup

COPY . /app/

RUN npm ci --ignore-scripts

RUN apt-get update && apt-get install -y dos2unix

RUN dos2unix /app/bin/build
RUN chmod +x /app/bin/build
RUN /app/bin/build

RUN dos2unix /app/bin/boot_server_in_docker
RUN chmod +x /app/bin/boot_server_in_docker

RUN cp /app/package.json /app/package.json.bak
ADD package.json /app/package.json
RUN npm ci --ignore-scripts
RUN cp -r /app/node_modules /app/node_modules.justserve
RUN cp /app/package.json.bak /app/package.json
RUN npm ci --ignore-scripts

RUN /app/bin/build

######################## - FINAL

FROM nginx:1.25.4-bookworm

RUN apt-get update \
  && apt-get clean -y \
  && apt-get install -y -q \
  libkrb5support0 \
  libexpat1 \
  libaom3 \
  && rm -rf /var/lib/apt/lists/*

RUN rm -rf /etc/nginx/conf.d/*
COPY docker_build/nginx.conf.template /var/tmp

COPY --from=setup /app/dist /usr/share/nginx/html
COPY --from=setup /app/bin /app/bin

CMD ["/app/bin/boot_server_in_docker"]