
net-start:
	docker network create elastic-net

net-stop:
	docker network rm elastic-net

elasticsearch-start:
	docker run -p 127.0.0.1:9200:9200 -d --name elasticsearch --network elastic-net --rm \
		-e ELASTIC_PASSWORD=$ELASTIC_PASSWORD \
		-e "discovery.type=single-node" \
		-e "xpack.security.http.ssl.enabled=false" \
		-e "xpack.license.self_generated.type=basic" \
		docker.elastic.co/elasticsearch/elasticsearch:8.14.3
	
elasticsearch-set-kibana-pwd:
	curl -u elastic:$ELASTIC_PASSWORD \
		-X POST \
		http://localhost:9200/_security/user/kibana_system/_password \
		-d '{"password":"'"$KIBANA_PASSWORD"'"}' \
		-H 'Content-Type: application/json'
	
elasticsearch-stop:
	docker stop elasticsearch

kibana-start:
	docker run -p 127.0.0.1:5601:5601 -d --name kibana --network elastic-net --rm \
		-e ELASTICSEARCH_URL=http://elasticsearch:9200 \
		-e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
		-e ELASTICSEARCH_USERNAME=kibana_system \
		-e ELASTICSEARCH_PASSWORD=$KIBANA_PASSWORD \
		-e "xpack.security.enabled=false" \
		-e "xpack.license.self_generated.type=trial" \
		docker.elastic.co/kibana/kibana:8.14.3
	
kibana-stop:
	docker stop kibana
	
events-demo-start: net-start elasticsearch-start
	@true
	
events-demo-stop: elasticsearch-stop net-stop
	@true
	
.PHONY: net-start net-stop \
	elasticsearch-start elasticsearch-set-kibana-pwd elasticsearch-stop \
	kibana-start kibana-stop \
	events-demo-start events-demo-stop
