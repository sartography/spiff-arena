USER_ID ?= $(shell id -u)
USER_NAME ?= $(shell id -un)
GROUP_ID ?= $(shell id -g)
GROUP_NAME ?= $(shell id -gn)
ME ?= $(USER_ID):$(GROUP_ID)

DEV_OVERLAYS ?= -f dev.docker-compose.yml
DOCKER_COMPOSE ?= RUN_AS=$(ME) docker compose -f docker-compose.yml $(DEV_OVERLAYS)

SERVICE ?= acp
EXEC_IN ?= $(DOCKER_COMPOSE) exec $(SERVICE)
RUN_IN ?= $(DOCKER_COMPOSE) run --rm $(SERVICE)

JUST ?=
PROFILE ?= speedscope

all: dev-env dev-start
	@true

build-images:
	$(DOCKER_COMPOSE) build \
		--build-arg USER_ID=$(USER_ID) \
		--build-arg USER_NAME=$(USER_NAME) \
		--build-arg GROUP_ID=$(GROUP_ID) \
		--build-arg GROUP_NAME=$(GROUP_NAME) \
		$(JUST)

dev-env: dev-stop build-images
	@true

dev-start: dev-stop
	$(DOCKER_COMPOSE) up -d
	
dev-stop:
	$(DOCKER_COMPOSE) down
	
logs:
	docker compose logs -f $(SERVICE)
	
sh:
	$(RUN_IN) /bin/bash

.PHONY: build-images \
	dev-start dev-stop \
	prof \
	logs sh
