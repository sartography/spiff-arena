MY_USER := $(shell id -u)
MY_GROUP := $(shell id -g)
ME := $(MY_USER):$(MY_GROUP)

BACKEND_CONTAINER ?= spiffworkflow-backend
BACKEND_DEV_OVERLAY ?= spiffworkflow-backend/dev.docker-compose.yml

FRONTEND_CONTAINER ?= spiffworkflow-frontend
FRONTEND_DEV_OVERLAY ?= spiffworkflow-frontend/dev.docker-compose.yml

YML_FILES := -f docker-compose.yml \
		-f $(BACKEND_DEV_OVERLAY) \
		-f $(FRONTEND_DEV_OVERLAY)

all: dev-env start-dev be-tests-par
	@/bin/true

dev-env:
	RUN_AS=$(ME) docker compose $(YML_FILES) build

start-dev: stop-dev
	RUN_AS=$(ME) docker compose $(YML_FILES) up -d

stop-dev:
	RUN_AS=$(ME) docker compose $(YML_FILES) down

be-sh:
	docker exec -it $(BACKEND_CONTAINER) /bin/bash

be-tests-par:
	docker exec -it $(BACKEND_CONTAINER) poetry run pytest -n auto -x --random-order

fe-lint-fix:
	docker exec -it $(FRONTEND_CONTAINER) npm run lint:fix

fe-sh:
	docker exec -it $(FRONTEND_CONTAINER) /bin/bash

take-ownership:
	sudo chown -R $(ME) .

.PHONY: dev-env start-dev stop-dev \
	be-sh be-tests-par \
	fe-lint-fix fe-sh \
	take-ownership
