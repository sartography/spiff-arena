FRONTEND_CONTAINER ?= spiffworkflow-frontend
FRONTEND_DEV_OVERLAY ?= spiffworkflow-frontend/dev.docker-compose.yml

dev-env:
	docker compose -f docker-compose.yml \
		-f $(FRONTEND_DEV_OVERLAY) \
		build

start-dev:
	docker compose -f docker-compose.yml \
		-f $(FRONTEND_DEV_OVERLAY) \
		up -d

stop-dev:
	docker compose -f docker-compose.yml \
		-f $(FRONTEND_DEV_OVERLAY) \
		down

fe-lint-fix:
	docker exec -it $(FRONTEND_CONTAINER) npm run lint:fix

fe-sh:
	docker exec -it $(FRONTEND_CONTAINER) /bin/bash

.PHONY: dev-env start-dev stop-dev \
	fe-lint-fix fe-sh
