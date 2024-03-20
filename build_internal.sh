#!/bin/bash
set -euxo pipefail
currentcommit=$(git rev-parse --short HEAD)
echo $currentcommit
make
docker tag ghcr.io/sartography/spiffworkflow-frontend:latest 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-frontent-${currentcommit}
docker tag ghcr.io/sartography/spiffworkflow-backend:latest 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-backend-${currentcommit}
docker tag ghcr.io/sartography/connector-proxy-demo:latest 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:connector-proxy-demo-${currentcommit}
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 607182506347.dkr.ecr.us-east-1.amazonaws.com
docker push 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-frontent-${currentcommit}
docker push 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-backend-${currentcommit}
docker push 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:connector-proxy-demo-${currentcommit}


