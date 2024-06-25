# Developer Setup

There are a few options here:

1. The make-based setup will spin up Docker containers and allow you to edit based on the latest source.
2. The docker-compose-based setup will spin up Docker containers based on the latest release and not allow you to edit.
3. The non-Docker setup will allow you to run the Python and React apps from your machine directly.

Please pick the one that best fits your needs.

## 1. Use the default make task

You can set up a full development environment for SpiffWorkflow like this:
```sh
git clone https://github.com/sartography/spiff-arena.git
cd spiff-arena
make
```

[This video](https://youtu.be/BvLvGt0fYJU?si=0zZSkzA1ZTotQxDb) shows what you can expect from the `make` setup.

## 2. Run the docker-compose setup

```sh
mkdir spiffworkflow
cd spiffworkflow
wget https://raw.githubusercontent.com/sartography/spiff-arena/main/docker-compose.yml
docker-compose pull
docker-compose up
```

There is a [Running SpiffWorkflow Locally with Docker](https://www.spiffworkflow.org/posts/articles/get_started_docker) blog post that accompanies this setup.

## 3. Non-Docker setup

Please see the instructions in the [spiff-arena README](https://github.com/sartography/spiff-arena/?tab=readme-ov-file#backend-setup-local).
