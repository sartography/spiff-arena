FROM python:3.12.1-slim-bookworm

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

RUN git config --global --add safe.directory /app

RUN pip install --upgrade pip
RUN pip install poetry==1.8.1
