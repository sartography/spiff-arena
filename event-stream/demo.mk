EVENTS_DEMO_CONTAINER ?= spiff-arena-event-stream-1
IN_EVENTS_DEMO ?= $(DOCKER_COMPOSE) run --rm $(EVENTS_DEMO_CONTAINER)
NETWORK ?= spiff-arena_default

ELASTIC_PASSWORD ?= elastic
KIBANA_PASSWORD ?= kibana


net-start:
	docker network create --label com.docker.compose.network=default $(NETWORK) || true

net-stop:
	docker network rm $(NETWORK) || true
	
elasticsearch-start:
	docker run -p 127.0.0.1:9200:9200 -d --name elasticsearch --network $(NETWORK) \
		-e ELASTIC_PASSWORD=$(ELASTIC_PASSWORD) \
		-e "discovery.type=single-node" \
		-e "xpack.security.http.ssl.enabled=false" \
		-e "xpack.license.self_generated.type=basic" \
		docker.elastic.co/elasticsearch/elasticsearch:8.14.3

elasticsearch-wait-for-boot:
	sleep 30
		
elasticsearch-create-index:
	curl -u elastic:$(ELASTIC_PASSWORD) \
		-X PUT \
		http://localhost:9200/events-index \
		-H 'Content-Type: application/json'
		
elasticsearch-kibana-set-pwd:
	curl -u elastic:$(ELASTIC_PASSWORD) \
		-X POST \
		http://localhost:9200/_security/user/kibana_system/_password \
		-d '{"password":"'"$(KIBANA_PASSWORD)"'"}' \
		-H 'Content-Type: application/json'
	
elasticsearch-stop:
	docker stop elasticsearch && docker container rm elasticsearch

kibana-start:
	docker run -p 127.0.0.1:5601:5601 -d --name kibana --network $(NETWORK) \
		-e ELASTICSEARCH_URL=http://elasticsearch:9200 \
		-e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
		-e ELASTICSEARCH_USERNAME=kibana_system \
		-e ELASTICSEARCH_PASSWORD=$(KIBANA_PASSWORD) \
		-e "xpack.security.enabled=false" \
		-e "xpack.license.self_generated.type=trial" \
		docker.elastic.co/kibana/kibana:8.14.3
	
kibana-stop:
	docker stop kibana && docker container rm kibana
	
events-demo-start: net-start \
	elasticsearch-start \
	elasticsearch-wait-for-boot \
	elasticsearch-create-index \
	elasticsearch-kibana-set-pwd \
	kibana-start
	@true
	
events-demo-stop: kibana-stop elasticsearch-stop net-stop
	@true

events-demo-logs:
	docker logs -f $(EVENTS_DEMO_CONTAINER)
	
events-demo-sh:
	$(IN_EVENTS_DEMO) /bin/bash

.PHONY: net-start net-stop \
	elasticsearch-start \
	elasticsearch-wait-for-boot \
	elasticsearch-create-index elasticsearch-kibana-set-pwd \
	elasticsearch-stop \
	kibana-start kibana-stop \
	events-demo-start events-demo-stop \
	events-demo-logs events-demo-sh
