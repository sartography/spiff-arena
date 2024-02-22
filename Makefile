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

.PHONY: dev-env start-dev stop-dev
