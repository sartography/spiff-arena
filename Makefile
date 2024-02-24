MY_USER := $(shell id -u)
MY_GROUP := $(shell id -g)
ME := $(MY_USER):$(MY_GROUP)

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

YML_FILES := -f docker-compose.yml \
	-f $(BACKEND_DEV_OVERLAY) \
	-f $(FRONTEND_DEV_OVERLAY) \
	-f $(ARENA_DEV_OVERLAY)

all: dev-env start-dev run-pyl
	@/bin/true

build-images:
	$(DOCKER_COMPOSE) build

dev-env: build-images fe-npm-i be-recreate-db
	@/bin/true

start-dev: stop-dev
	$(DOCKER_COMPOSE) up -d

stop-dev:
	$(DOCKER_COMPOSE) down

be-clear-log-file:
	$(IN_BACKEND) rm -f log/unit_testing.log

be-mypy:
	$(IN_BACKEND) poetry run mypy src tests

be-recreate-db:
	$(IN_BACKEND) ./bin/recreate_db clean

be-ruff:
	$(IN_BACKEND) poetry run ruff --fix .

be-sh:
	$(IN_BACKEND) /bin/bash

be-tests: be-clear-log-file
	$(IN_BACKEND) poetry run pytest

be-tests-par: be-clear-log-file
	$(IN_BACKEND) poetry run pytest -n auto -x --random-order

fe-lint-fix:
	$(IN_FRONTEND) npm run lint:fix

fe-npm-i:
	$(IN_FRONTEND) npm i

fe-sh:
	$(IN_FRONTEND) /bin/bash

pre-commit:
	$(IN_ARENA) poetry run pre-commit run --verbose --all-files

run-pyl: fe-lint-fix pre-commit be-mypy be-tests-par
	@/bin/true

sh:
	$(IN_ARENA) /bin/bash

take-ownership:
	sudo chown -R $(ME) .

.PHONY: build-images dev-env \
	start-dev stop-dev \
	be-clear-log-file be-recreate-db be-ruff be-sh be-tests be-tests-par \
	fe-lint-fix fe-npm-i fe-sh \
	pre-commit run-pyl \
	take-ownership
