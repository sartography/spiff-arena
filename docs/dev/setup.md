# Developer Setup

There are a few options here:

1. The make-based setup will spin up Docker containers and allow you to edit based on the latest source.
2. The docker-compose-based setup will spin up Docker containers based on the latest release and not allow you to edit.
3. The non-Docker setup will allow you to run the Python and React apps from your machine directly.
4. Set up in a Windows environment using Docker Desktop

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

## 4. Running Windows?
* Install Docker desktop app 
* Install Git
* Fire up a PowerShell and clone the repo of Spiff arena:  
```sh
 git clone  https://github.com/sartography/spiff-arena.git  
 cd spiff-arena 
```
* Modify the following file in your checkout "spiff-arena\docker-compose.yml" 
* you want find the environment variable below, and change it to your ip
  address.
```sh
SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL: "${SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL:-http://[YOUR_IP_ADDRESS]:8004}" 
```
* Open Powershell in admin mode 
* Type the following: 
```
cd C:\Users\[YOUR_USER]\Documents\GitHub\spiff-arena 
docker compose up (build) 
```

## BONUS: Running your own connector proxy to create custom connections to other software and systems on your network

* Modify the following file in your spiff-arena git checkout "spiff-arena\docker-compose.yml"
* you want find the environment variable below, and change it to your ip address.
```sh
SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL: "${SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL:-http://[YOUR_IP_ADDRESS]:8004}"
```
* Copy the folder named connector-proxy-demo from your spiff-arena git checkout
  to a new directory - this will be YOUR connector proxy, you might create a new
git repo for it.
* Assure you have a recent version of python installed
* run pip install
* flask run -p 8004 --host=0.0.0.0 (to turn it off press CTRL + C) 
* You can now create your connectors and they will show up when you edit
  services tasks and select the service you want to call.

