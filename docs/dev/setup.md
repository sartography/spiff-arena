# Developer Setup


There are few options here:

 1. The make-based setup will spin up docker containers and allow you to edit based on latest source.
 2. The docker-compose-based setup will spin up docker containers based on the latest release and not allow you to edit.
 3. The non-docker setup will allow you to run the python and react apps from your machine directly.

Please pick the one that best fits your needs.
## Use the default make task
You can set up a full development environment for SpiffWorkflow like this:
```sh
git clone https://github.com/sartography/spiff-arena.git
cd spiff-arena
make
```

[This video](https://youtu.be/BvLvGt0fYJU?si=0zZSkzA1ZTotQxDb) shows what you can expect from the `make` setup.

## Run the docker compose setup

```sh
mkdir spiffworkflow
cd spiffworkflow
wget https://raw.githubusercontent.com/sartography/spiff-arena/main/docker-compose.yml
docker-compose pull
docker-compose up
```

There is a [Running SpiffWorkflow Locally with Docker](https://www.spiffworkflow.org/posts/articles/get_started_docker) blog post that accompanies this setup.

## Non-docker setup

Please see the instructions in the [spiff-arena README](https://github.com/sartography/spiff-arena/?tab=readme-ov-file#backend-setup-local).
