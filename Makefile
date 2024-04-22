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

BACKEND_SQLITE_FILE ?= src/instance/db_$(SPIFFWORKFLOW_BACKEND_ENV).sqlite3
NODE_MODULES_DIR ?= spiffworkflow-frontend/node_modules
JUST ?=

YML_FILES := -f docker-compose.yml \
	-f $(BACKEND_DEV_OVERLAY) \
	-f $(FRONTEND_DEV_OVERLAY) \
	-f $(ARENA_DEV_OVERLAY)

all: dev-env start-dev run-pyl
	@true

build-images:
	$(DOCKER_COMPOSE) build

dev-env: stop-dev build-images poetry-i be-poetry-i be-db-clean fe-npm-i
	@true

start-dev: stop-dev
	$(DOCKER_COMPOSE) up -d

stop-dev:
	$(DOCKER_COMPOSE) down

be-clear-log-file:
	$(IN_BACKEND) rm -f log/unit_testing.log

be-db-clean:
	$(IN_BACKEND) ./bin/recreate_db clean

be-db-migrate:
	$(IN_BACKEND) ./bin/recreate_db migrate

be-logs:
	docker logs -f $(BACKEND_CONTAINER)

be-mypy:
	$(IN_BACKEND) poetry run mypy src tests

be-poetry-i:
	$(IN_BACKEND) poetry install

be-poetry-lock:
	$(IN_BACKEND) poetry lock --no-update

be-poetry-rm:
	@if [ -d "$(BACKEND_CONTAINER)/.venv" ]; then \
		rm -rf "$(BACKEND_CONTAINER)/.venv"; \
	fi

be-sh:
	$(IN_BACKEND) /bin/bash

be-sqlite:
	@if [ ! -f "$(BACKEND_CONTAINER)/$(BACKEND_SQLITE_FILE)" ]; then \
		echo "SQLite database file does not exist: $(BACKEND_CONTAINER)/$(BACKEND_SQLITE_FILE)"; \
		exit 1; \
	fi
	$(IN_BACKEND) sqlite3 $(BACKEND_SQLITE_FILE)

be-tests: be-clear-log-file
	$(IN_BACKEND) poetry run pytest tests/spiffworkflow_backend/$(JUST)

be-tests-par: be-clear-log-file
	$(IN_BACKEND) poetry run pytest -n auto -x --random-order tests/spiffworkflow_backend/$(JUST)

fe-lint-fix:
	$(IN_FRONTEND) npm run lint:fix

fe-logs:
	docker logs -f $(FRONTEND_CONTAINER)

fe-npm-clean:
	@if [ -d "$(NODE_MODULES_DIR)" ]; then \
		rm -rf "$(NODE_MODULES_DIR)"; \
	fi

fe-npm-i:
	$(IN_FRONTEND) npm i && git checkout -- spiffworkflow-frontend/package-lock.json

fe-npm-rm:
	$(IN_FRONTEND) npm rm $(JUST)

fe-sh:
	$(IN_FRONTEND) /bin/bash

fe-unimported:
	$(IN_FRONTEND) npx unimported

poetry-i:
	$(IN_ARENA) poetry install --no-root

poetry-rm:
	@if [ -d ".venv" ]; then \
		rm -rf ".venv"; \
	fi

pre-commit:
	$(IN_ARENA) poetry run pre-commit run --verbose --all-files

ruff:
	$(IN_ARENA) poetry run ruff check --fix spiffworkflow-backend

run-pyl: fe-lint-fix ruff pre-commit be-mypy be-tests-par
	@true

sh:
	$(IN_ARENA) /bin/bash

take-ownership:
	$(SUDO) chown -R $(ME) .

.PHONY: build-images dev-env \
	start-dev stop-dev \
	be-clear-log-file be-logs be-mypy be-poetry-i be-poetry-lock be-poetry-rm \
	be-db-clean be-db-migrate be-sh be-sqlite be-tests be-tests-par \
	fe-lint-fix fe-logs fe-npm-clean fe-npm-i fe-npm-rm fe-sh fe-unimported  \
	poetry-i poetry-rm pre-commit ruff run-pyl \
	take-ownership
