MY_USER := $(shell id -u)
MY_GROUP := $(shell id -g)
ME := $(MY_USER):$(MY_GROUP)

SUDO ?= sudo

ARENA_CONTAINER ?= spiff-arena
ARENA_DEV_OVERLAY ?= dev.docker-compose.yml

BACKEND_CONTAINER ?= spiffworkflow-backend
BACKEND_DEV_OVERLAY ?= spiffworkflow-backend/dev.docker-compose.yml

FRONTEND_CONTAINER ?= spiffworkflow-frontend
FRONTEND_DEV_OVERLAY ?= spiffworkflow-frontend/dev.docker-compose.yml

DOCKER_COMPOSE ?= RUN_AS=$(ME) docker compose $(YML_FILES)
IN_ARENA ?= $(DOCKER_COMPOSE) run $(ARENA_CONTAINER)
IN_BACKEND ?= $(DOCKER_COMPOSE) run $(BACKEND_CONTAINER)
IN_FRONTEND ?= $(DOCKER_COMPOSE) run $(FRONTEND_CONTAINER)

SPIFFWORKFLOW_BACKEND_ENV ?= local_development

YML_FILES := -f docker-compose.yml \
	-f $(BACKEND_DEV_OVERLAY) \
	-f $(FRONTEND_DEV_OVERLAY) \
	-f $(ARENA_DEV_OVERLAY)

all: dev-env start-dev run-pyl
	@/bin/true

build-images:
	$(DOCKER_COMPOSE) build

dev-env: stop-dev build-images poetry-i be-poetry-i be-recreate-db fe-npm-i
	@/bin/true

start-dev: stop-dev
	$(DOCKER_COMPOSE) up -d

stop-dev:
	$(DOCKER_COMPOSE) down

be-clear-log-file:
	$(IN_BACKEND) rm -f log/unit_testing.log

be-logs:
	docker logs -f $(BACKEND_CONTAINER)

be-mypy:
	$(IN_BACKEND) poetry run mypy src tests

be-poetry-i:
	$(IN_BACKEND) poetry install

be-recreate-db:
	$(IN_BACKEND) ./bin/recreate_db clean

be-ruff:
	$(IN_BACKEND) poetry run ruff --fix .

be-sh:
	$(IN_BACKEND) /bin/bash

be-sqlite:
	@if [ ! -f "$(BACKEND_CONTAINER)/src/instance/db_$(SPIFFWORKFLOW_BACKEND_ENV).sqlite3" ]; then \
		echo "SQLite database file does not exist: $(BACKEND_CONTAINER)/src/instance/db_$(SPIFFWORKFLOW_BACKEND_ENV).sqlite3"; \
	exit 1; \
	fi
	$(IN_BACKEND) sqlite3 src/instance/db_$(SPIFFWORKFLOW_BACKEND_ENV).sqlite3

be-tests: be-clear-log-file
	$(IN_BACKEND) poetry run pytest

be-tests-par: be-clear-log-file
	$(IN_BACKEND) poetry run pytest -n auto -x --random-order

fe-lint-fix:
	$(IN_FRONTEND) npm run lint:fix

fe-logs:
	docker logs -f $(FRONTEND_CONTAINER)

fe-npm-i:
	$(IN_FRONTEND) npm i && git checkout -- spiffworkflow-frontend/package-lock.json

fe-sh:
	$(IN_FRONTEND) /bin/bash

poetry-i:
	$(IN_ARENA) poetry install --no-root

pre-commit:
	$(IN_ARENA) poetry run pre-commit run --verbose --all-files

run-pyl: fe-lint-fix pre-commit be-mypy be-tests-par
	@/bin/true

sh:
	$(IN_ARENA) /bin/bash

take-ownership:
	$(SUDO) chown -R $(ME) .

.PHONY: build-images dev-env \
	start-dev stop-dev \
	be-clear-log-file be-logs be-mypy be-poetry-i be-recreate-db be-ruff be-sh be-sqlite be-tests be-tests-par \
	fe-lint-fix fe-logs fe-npm-i fe-sh \
	poetry-i pre-commit run-pyl \
	take-ownership
