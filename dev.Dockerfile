FROM python:3.12.1-slim-bookworm

WORKDIR /app

RUN apt-get update \
 && apt-get install -y -q git-core curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /app

RUN pip install --upgrade pip
RUN pip install poetry==1.8.1