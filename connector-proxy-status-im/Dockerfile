FROM ghcr.io/sartography/python:3.10

RUN pip install poetry
RUN useradd _gunicorn --no-create-home --user-group

WORKDIR /app
ADD pyproject.toml poetry.lock /app/
ADD connectors /app/connectors
RUN poetry install

RUN set -xe \
  && apt-get remove -y gcc python3-dev libssl-dev \
  && apt-get autoremove -y \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/*

COPY . /app/

# run poetry install again AFTER copying the app into the image
# otherwise it does not know what the main app module is
RUN poetry install

CMD ./bin/boot_server_in_docker
