#!/usr/bin/env bash

set -eo pipefail

script_dir="$(
  cd -- "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

# Check if CIVI environment variable is set
if [ -z "${CIVI:-}" ]; then
  echo "Error: CIVI environment variable is not set"
  echo "Please set it with: export CIVI=your_api_key"
  exit 1
fi

# Default values
NUM_TASKS=${NUM_TASKS:-5}
API_HOST=${API_HOST:-host.docker.internal:7000}

echo "=========================================="
echo "Parallel Manual Tasks Load Test"
echo "=========================================="
echo "Number of tasks: ${NUM_TASKS}"
echo "API Host: ${API_HOST}"
echo "Starting test..."
echo ""

# Run k6 test
docker run --rm --add-host=host.docker.internal:host-gateway -i grafana/k6 \
  -e SPIFF_API_KEY="$CIVI" \
  -e API_HOST="$API_HOST" \
  -e NUM_TASKS="$NUM_TASKS" \
  run -u "$NUM_TASKS" -i "$NUM_TASKS" - <"${script_dir}/parallel_tasks.js"

echo ""
echo "Test completed!"