BACKEND_CONTAINER ?= spiffworkflow-backend
BACKEND_DEV_OVERLAY ?= spiffworkflow-backend/dev.docker-compose.yml

FRONTEND_CONTAINER ?= spiffworkflow-frontend
FRONTEND_DEV_OVERLAY ?= spiffworkflow-frontend/dev.docker-compose.yml

YML_FILES := -f docker-compose.yml \
		-f $(BACKEND_DEV_OVERLAY) \
		-f $(FRONTEND_DEV_OVERLAY)

dev-env:
	docker compose $(YML_FILES) build

start-dev: stop-dev
	docker compose $(YML_FILES) up -d

stop-dev:
	docker compose $(YML_FILES) down

be-sh:
	docker exec -it $(BACKEND_CONTAINER) /bin/bash

be-tests-par:
	docker exec -it $(BACKEND_CONTAINER) poetry run pytest -n auto -x --random-order

fe-lint-fix:
	docker exec -it $(FRONTEND_CONTAINER) npm run lint:fix

fe-sh:
	docker exec -it $(FRONTEND_CONTAINER) /bin/bash

.PHONY: dev-env start-dev stop-dev \
	be-sh be-tests-par \
	fe-lint-fix fe-sh
