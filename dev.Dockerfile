FROM python:3.12.1-slim-bookworm

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry==1.6.1

COPY pyproject.toml poetry.lock .
RUN poetry install --no-root

CMD ["/bin/true"]
