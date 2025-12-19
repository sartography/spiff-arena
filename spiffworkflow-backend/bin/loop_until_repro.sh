#!/usr/bin/env bash

function error_handler() {
  echo >&2 "Exited with BAD EXIT CODE '${2}' in ${0} script at line: ${1}."
  exit "$2"
}
trap 'error_handler ${LINENO} $?' ERR
set -o errtrace -o errexit -o nounset -o pipefail

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

echo "Starting loop to reproduce race condition..."
echo "Will run until the issue is detected or you press Ctrl+C"
echo ""

attempt=0

while true; do
  attempt=$((attempt + 1))
  echo "=========================================="
  echo "Attempt #${attempt} - $(date)"
  echo "=========================================="
  
  # Clean up all process and message instances
  echo "Cleaning up database..."
  "${script_dir}/run_local_python_script" "${script_dir}/delete_all_process_and_message_instances.py"
  
  echo ""
  echo "Running k6 test..."
  
  # Run k6 test and capture exit code
  set +e
  docker run --rm -i grafana/k6 \
    -e SPIFF_API_KEY="$CIVI" \
    -e API_HOST=host.docker.internal:7000 \
    run -u 60 -i 60 - < "${script_dir}/m3.js"
  k6_exit_code=$?
  set -e
  
  # k6 exits with code 108 when exec.test.abort() is called
  if [ $k6_exit_code -eq 108 ]; then
    echo ""
    echo "🎯 SUCCESS! Race condition reproduced on attempt #${attempt}"
    echo ""
    echo "Checking database for confirmation..."
    mysql -uroot spiffworkflow_backend_local_development -e \
      'select id, created_at, endpoint, method, process_instance_id, request_body, status_code from api_log where response_body like "%This process is not waiting for two%" order by id desc limit 10'
    echo ""
    echo "Race condition successfully reproduced!"
    exit 0
  elif [ $k6_exit_code -ne 0 ]; then
    echo "Warning: k6 exited with code ${k6_exit_code} (not the race condition)"
  fi
  
  echo ""
  echo "No race condition detected on attempt #${attempt}. Trying again..."
  echo ""
  sleep 1
done
