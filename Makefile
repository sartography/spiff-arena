MY_USER := $(shell id -u)
MY_GROUP := $(shell id -g)
ME := $(MY_USER):$(MY_GROUP)

BACKEND_CONTAINER ?= spiffworkflow-backend
BACKEND_DEV_OVERLAY ?= spiffworkflow-backend/dev.docker-compose.yml

FRONTEND_CONTAINER ?= spiffworkflow-frontend
FRONTEND_DEV_OVERLAY ?= spiffworkflow-frontend/dev.docker-compose.yml

DOCKER_COMPOSE ?= RUN_AS=$(ME) docker compose $(YML_FILES)
IN_BACKEND ?= $(DOCKER_COMPOSE) run $(BACKEND_CONTAINER)
IN_FRONTEND ?= $(DOCKER_COMPOSE) run $(FRONTEND_CONTAINER)

YML_FILES := -f docker-compose.yml \
		-f $(BACKEND_DEV_OVERLAY) \
		-f $(FRONTEND_DEV_OVERLAY)

all: dev-env start-dev be-tests-par
	@/bin/true

build-images:
	$(DOCKER_COMPOSE) build

dev-env: build-images be-recreate-db
	@/bin/true

start-dev: stop-dev
	$(DOCKER_COMPOSE) up -d

stop-dev:
	$(DOCKER_COMPOSE) down

be-recreate-db:
	$(IN_BACKEND) ./bin/recreate_db clean

be-sh:
	$(IN_BACKEND) /bin/bash

be-tests:
	$(IN_BACKEND) poetry run pytest

be-tests-par:
	$(IN_BACKEND) poetry run pytest -n auto -x --random-order

fe-lint-fix:
	$(IN_FRONTEND) npm run lint:fix

fe-sh:
	$(IN_FRONTEND) /bin/bash

take-ownership:
	sudo chown -R $(ME) .

.PHONY: build-images dev-env \
	start-dev stop-dev \
	be-recreate-db be-sh be-tests be-tests-par \
	fe-lint-fix fe-sh \
	take-ownership
