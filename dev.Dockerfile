FROM python:3.14.6-slim-trixie@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6

ARG USER_ID
ARG USER_NAME
ARG GROUP_ID
ARG GROUP_NAME

WORKDIR /app

RUN apt-get update \
  && apt-get install -y -q git-core curl vim-tiny \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN if ! getent group "$GROUP_ID"; then addgroup --gid $GROUP_ID $GROUP_NAME; fi
RUN adduser --uid $USER_ID --gid $GROUP_ID $USER_NAME

RUN git config --global --add safe.directory *

RUN pip install --upgrade pip
RUN pip install uv==0.10.0
