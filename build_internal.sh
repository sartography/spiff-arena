#!/bin/bash
set -euxo pipefail
currentcommit=$(git rev-parse --short HEAD)
echo $currentcommit
docker build ./connector-proxy-demo -t 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:connector-proxy-demo-${currentcommit}
docker build ./spiffworkflow-frontend -t 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-frontend-${currentcommit}
docker build ./spiffworkflow-backend -t 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-backend-${currentcommit}
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 607182506347.dkr.ecr.us-east-1.amazonaws.com
docker push 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:connector-proxy-demo-${currentcommit}
docker push 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-frontend-${currentcommit}
docker push 607182506347.dkr.ecr.us-east-1.amazonaws.com/spiff:spiffworkflow-backend-${currentcommit}


