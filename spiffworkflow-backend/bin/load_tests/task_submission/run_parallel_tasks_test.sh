#!/usr/bin/env bash

set -eo pipefail

script_dir="$(
  cd -- "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

# Default values
NUM_TASKS=${NUM_TASKS:-5}
API_HOST=${API_HOST:-host.docker.internal:7000}
BACKEND_BASE_URL=${BACKEND_BASE_URL:-http://localhost:7000}
BACKEND_BASE_URL=${BACKEND_BASE_URL%/}
PROCESS_GROUP_ID=${PROCESS_GROUP_ID:-load_test/task_submission_$(date +%s)_$$}
PROCESS_MODEL_ID=${PROCESS_MODEL_ID:-${PROCESS_GROUP_ID}/parallel-task}
PRIMARY_FILE_NAME=${PRIMARY_FILE_NAME:-parallel-task.bpmn}
PRIMARY_PROCESS_ID=${PRIMARY_PROCESS_ID:-Process_parallel_task_eyeplo6}
MESSAGE_NAME=${MESSAGE_NAME:-start-parallel-task-process}
SKIP_DB_CHECKS=${SKIP_DB_CHECKS:-false}
DB_CHECKS=${DB_CHECKS:-auto}
MYSQL_DATABASE=${MYSQL_DATABASE:-spiffworkflow_backend_local_development}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_HOST=${MYSQL_HOST:-}
AUTH_METHOD=${AUTH_METHOD:-token}
USERNAME=${USERNAME:-admin}
PASSWORD=${PASSWORD:-admin}
CLIENT_ID=${CLIENT_ID:-spiffworkflow-backend}
CLIENT_SECRET=${CLIENT_SECRET:-JXeQExm0JhQPLumgHtIIqf52bDalHz0q}
OPENID_TOKEN_URL=${OPENID_TOKEN_URL:-${BACKEND_BASE_URL}/openid/token}
AUTHENTICATION_IDENTIFIER=${AUTHENTICATION_IDENTIFIER:-default}
ACCESS_TOKEN=${ACCESS_TOKEN:-}
AUTH_HEADER_NAME=""
AUTH_HEADER_VALUE=""

mysql_args=(-u"$MYSQL_USER")
if [[ -n "$MYSQL_HOST" ]]; then
  mysql_args+=(-h "$MYSQL_HOST")
fi
mysql_args+=("$MYSQL_DATABASE")

function modified_identifier() {
  tr '/' ':' <<<"$1"
}

function response_body() {
  sed '$d' <<<"$1"
}

function response_status() {
  tail -n 1 <<<"$1"
}

function curl_with_status() {
  local method="$1"
  local url="$2"
  shift 2
  curl --silent --show-error -X "$method" "$url" \
    -H "${AUTH_HEADER_NAME}: ${AUTH_HEADER_VALUE}" \
    "$@" \
    --write-out $'\n%{http_code}'
}

function json_value() {
  local key="$1"
  uv run python -c 'import json, sys; print(json.load(sys.stdin).get(sys.argv[1], ""))' "$key"
}

function get_access_token() {
  local basic_auth result status body access_token

  if [[ -n "$ACCESS_TOKEN" ]]; then
    echo "$ACCESS_TOKEN"
    return
  fi

  basic_auth=$(printf "%s:%s" "$CLIENT_ID" "$CLIENT_SECRET" | base64 | tr -d '\n')
  result=$(curl --silent --show-error -X POST "$OPENID_TOKEN_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "Authorization: Basic ${basic_auth}" \
    --data-urlencode "grant_type=password" \
    --data-urlencode "code=${USERNAME}:this_is_not_secure_do_not_use_in_production" \
    --data-urlencode "username=${USERNAME}" \
    --data-urlencode "password=${PASSWORD}" \
    --data-urlencode "client_id=${CLIENT_ID}" \
    --write-out $'\n%{http_code}')
  status=$(response_status "$result")
  body=$(response_body "$result")
  if [[ "$status" != "200" ]]; then
    echo >&2 "ERROR: Could not get access token from ${OPENID_TOKEN_URL}. Result was: ${body}"
    exit 1
  fi

  access_token=$(json_value access_token <<<"$body")
  if [[ -z "$access_token" ]]; then
    echo >&2 "ERROR: Token response did not include access_token. Result was: ${body}"
    exit 1
  fi
  echo "$access_token"
}

function configure_auth() {
  local token result status body

  case "$AUTH_METHOD" in
    token)
      token=$(get_access_token)
      AUTH_HEADER_NAME="Authorization"
      AUTH_HEADER_VALUE="Bearer ${token}"

      result=$(curl_with_status POST "${BACKEND_BASE_URL}/v1.0/login_with_access_token?authentication_identifier=${AUTHENTICATION_IDENTIFIER}")
      status=$(response_status "$result")
      body=$(response_body "$result")
      if [[ "$status" != "200" && "$status" != "204" && "$status" != "302" ]]; then
        echo >&2 "ERROR: Could not log in with access token. Result was: ${body}"
        exit 1
      fi
      ;;
    api_key)
      if [[ -z "${SPIFF_API_KEY:-}" ]]; then
        echo "Error: SPIFF_API_KEY is required when AUTH_METHOD=api_key"
        exit 1
      fi
      AUTH_HEADER_NAME="SpiffWorkflow-Api-Key"
      AUTH_HEADER_VALUE="$SPIFF_API_KEY"
      ;;
    *)
      echo "Error: AUTH_METHOD must be token or api_key. Got '${AUTH_METHOD}'."
      exit 1
      ;;
  esac
}

function ensure_process_group() {
  local process_group_id="$1"
  local result status body payload

  payload=$(printf '{"id":"%s","display_name":"%s","description":"Temporary group for parallel task submission load testing","display_order":0,"admin":false}' "$process_group_id" "$process_group_id")
  result=$(curl_with_status POST "${BACKEND_BASE_URL}/v1.0/process-groups" -H "Content-Type: application/json" --data "$payload")
  status=$(response_status "$result")
  body=$(response_body "$result")

  if [[ "$status" != "201" && ! ("$status" == "400" && "$body" == *"already_exists"*) ]]; then
    echo >&2 "ERROR: Could not create process group ${process_group_id}. Result was: ${body}"
    exit 1
  fi
}

function ensure_process_group_path() {
  local process_group_id="$1"
  local current_group=""
  local part

  IFS='/' read -ra group_parts <<<"$process_group_id"
  for part in "${group_parts[@]}"; do
    if [[ -z "$current_group" ]]; then
      current_group="$part"
    else
      current_group="${current_group}/${part}"
    fi
    ensure_process_group "$current_group"
  done
}

function ensure_process_model() {
  local process_group_id="$1"
  local modified_process_group_id modified_process_model_id result status body payload

  modified_process_group_id=$(modified_identifier "$process_group_id")
  modified_process_model_id=$(modified_identifier "$PROCESS_MODEL_ID")

  payload=$(printf '{"id":"%s","display_name":"%s","description":"Temporary model for parallel task submission load testing","fault_or_suspend_on_exception":"fault","exception_notification_addresses":[]}' "$PROCESS_MODEL_ID" "${PROCESS_MODEL_ID##*/}")
  result=$(curl_with_status POST "${BACKEND_BASE_URL}/v1.0/process-models/${modified_process_group_id}" -H "Content-Type: application/json" --data "$payload")
  status=$(response_status "$result")
  body=$(response_body "$result")
  if [[ "$status" != "201" && ! ("$status" == "400" && "$body" == *"already_exists"*) ]]; then
    echo >&2 "ERROR: Could not create process model ${PROCESS_MODEL_ID}. Result was: ${body}"
    exit 1
  fi

  result=$(curl_with_status PUT "${BACKEND_BASE_URL}/v1.0/process-models/${modified_process_model_id}/files/${PRIMARY_FILE_NAME}" -F "file=@${script_dir}/${PRIMARY_FILE_NAME};filename=${PRIMARY_FILE_NAME};type=text/xml")
  status=$(response_status "$result")
  body=$(response_body "$result")
  if [[ "$status" != "200" ]]; then
    echo >&2 "ERROR: Could not upload ${PRIMARY_FILE_NAME}. Result was: ${body}"
    exit 1
  fi

  payload=$(printf '{"primary_file_name":"%s","primary_process_id":"%s","display_name":"%s","description":"Temporary model for parallel task submission load testing","fault_or_suspend_on_exception":"fault","exception_notification_addresses":[]}' "$PRIMARY_FILE_NAME" "$PRIMARY_PROCESS_ID" "${PROCESS_MODEL_ID##*/}")
  result=$(curl_with_status PUT "${BACKEND_BASE_URL}/v1.0/process-models/${modified_process_model_id}" -H "Content-Type: application/json" --data "$payload")
  status=$(response_status "$result")
  body=$(response_body "$result")
  if [[ "$status" != "200" ]]; then
    echo >&2 "ERROR: Could not set primary BPMN for ${PROCESS_MODEL_ID}. Result was: ${body}"
    exit 1
  fi
}

function mysql_query() {
  mysql "${mysql_args[@]}" -e "$1"
}

function mysql_scalar_query() {
  mysql "${mysql_args[@]}" --batch --skip-column-names -e "$1"
}

process_group_id="${PROCESS_MODEL_ID%/*}"
if [[ "$process_group_id" == "$PROCESS_MODEL_ID" ]]; then
  echo "Error: PROCESS_MODEL_ID must include a process group, for example load_test/task_submission/parallel-task"
  exit 1
fi
modified_message_name="$(modified_identifier "$process_group_id"):${MESSAGE_NAME}"
configure_auth

echo "=========================================="
echo "Parallel Manual Tasks Load Test"
echo "=========================================="
echo "Number of tasks to create: ${NUM_TASKS}"
echo "Number of concurrent VUs: ${NUM_TASKS}"
echo "API Host: ${API_HOST}"
echo "Backend Base URL: ${BACKEND_BASE_URL}"
echo "Auth Method: ${AUTH_METHOD}"
echo "Process Model: ${PROCESS_MODEL_ID}"
echo "Message: ${modified_message_name}"
echo "Starting test..."
echo ""

echo "Ensuring temporary process model exists..."
ensure_process_group_path "$process_group_id"
ensure_process_model "$process_group_id"
echo "Process model is ready."
echo ""

# Run k6 test and capture exit code and output
set +e
k6_output=$(docker run --rm --add-host=host.docker.internal:host-gateway -i grafana/k6 \
  -e AUTH_HEADER_NAME="$AUTH_HEADER_NAME" \
  -e AUTH_HEADER_VALUE="$AUTH_HEADER_VALUE" \
  -e API_HOST="$API_HOST" \
  -e NUM_TASKS="$NUM_TASKS" \
  -e MODIFIED_MESSAGE_NAME="$modified_message_name" \
  run -u "$NUM_TASKS" -i "$NUM_TASKS" - <"${script_dir}/parallel_tasks.js" 2>&1)
k6_exit_code=$?
set -e

# Display the k6 output
echo "$k6_output"

# Extract process instance ID from k6 output
process_instance_id_raw=$(echo "$k6_output" | grep "PROCESS_INSTANCE_ID_FOR_BASH:" | sed 's/.*PROCESS_INSTANCE_ID_FOR_BASH: //' | head -1)

# Clean the process instance ID (remove any extra characters, whitespace, etc.)
process_instance_id=$(echo "$process_instance_id_raw" | tr -d '\r\n' | sed 's/[^0-9]//g')

echo "DEBUG: Raw process instance ID: '$process_instance_id_raw'"
echo "DEBUG: Cleaned process instance ID: '$process_instance_id'"

if [ -z "$process_instance_id" ] || [ "$process_instance_id" = "" ]; then
  echo "⚠️  Could not extract process instance ID from k6 output"
  echo "Skipping database checks"
  exit $k6_exit_code
fi

# Validate it's a number
if ! [[ "$process_instance_id" =~ ^[0-9]+$ ]]; then
  echo "⚠️  Process instance ID is not a valid number: '$process_instance_id'"
  echo "Skipping database checks"
  exit $k6_exit_code
fi

echo ""
echo "Test completed with exit code: ${k6_exit_code}"
echo "Process Instance ID: ${process_instance_id}"
echo ""
echo "Checking database for race condition indicators..."

if [[ "$SKIP_DB_CHECKS" == "true" || "$SKIP_DB_CHECKS" == "1" ]]; then
  echo "Skipping database checks because SKIP_DB_CHECKS=${SKIP_DB_CHECKS}"
  exit $k6_exit_code
fi

if [[ "$DB_CHECKS" == "never" ]]; then
  echo "Skipping database checks because DB_CHECKS=never"
  exit $k6_exit_code
fi

if ! command -v mysql >/dev/null 2>&1; then
  echo "Skipping database checks because mysql is not available on PATH"
  exit $k6_exit_code
fi

if [[ "$DB_CHECKS" == "auto" ]]; then
  process_instance_row_count=$(mysql_scalar_query "SELECT COUNT(*) FROM process_instance WHERE id = ${process_instance_id};" 2>/dev/null || true)
  if [[ "$process_instance_row_count" != "1" ]]; then
    echo "Skipping database checks because process instance ${process_instance_id} was not found in MySQL database ${MYSQL_DATABASE}"
    echo "Set DB_CHECKS=always to force MySQL diagnostics, or MYSQL_DATABASE/MYSQL_USER/MYSQL_HOST to point at the backend MySQL database."
    exit $k6_exit_code
  fi
elif [[ "$DB_CHECKS" != "always" ]]; then
  echo "Error: DB_CHECKS must be one of auto, always, or never. Got '${DB_CHECKS}'."
  exit 1
fi

# Check for duplicate human task records by task GUID (the race condition we're looking for)
echo "=== 🔍 RACE CONDITION CHECK: Multiple human_task records per task GUID ==="
mysql_query "SELECT task_id, COUNT(*) as human_task_count, GROUP_CONCAT(id ORDER BY id) as human_task_record_ids, GROUP_CONCAT(created_at_in_seconds ORDER BY id) as created_timestamps FROM human_task WHERE process_instance_id = ${process_instance_id} GROUP BY task_id HAVING COUNT(*) > 1 ORDER BY human_task_count DESC;"

# Extract ProcessInstanceIsAlreadyLockedError occurrences
lock_errors=$(echo "$k6_output" | grep "LOCK_ERROR_FOR_BASH:" || true)
if [ -n "$lock_errors" ]; then
  echo ""
  echo "=== 🔒 ProcessInstanceIsAlreadyLockedError DETECTED ==="
  echo "$lock_errors"
  lock_error_count=$(echo "$lock_errors" | wc -l)
  echo "Total lock errors: $lock_error_count"
else
  echo ""
  echo "=== 🔒 Lock Error Check ==="
  echo "No ProcessInstanceIsAlreadyLockedError detected in responses"
fi

echo ""
echo "=== All human tasks for process instance ${process_instance_id} ==="
mysql_query "SELECT id, task_id, process_instance_id, task_name, task_title, completed, created_at_in_seconds, FROM_UNIXTIME(created_at_in_seconds) as created_at FROM human_task WHERE process_instance_id = ${process_instance_id} ORDER BY task_id, created_at_in_seconds ASC;"

echo ""
echo "=== Summary: Human task counts by task GUID ==="
mysql_query "SELECT task_id, COUNT(*) as human_task_count, GROUP_CONCAT(CASE WHEN completed = 1 THEN 'COMPLETED' ELSE 'PENDING' END) as completion_status, CASE WHEN COUNT(*) > 1 THEN 'DUPLICATE - RACE CONDITION!' ELSE 'Normal' END as status FROM human_task WHERE process_instance_id = ${process_instance_id} GROUP BY task_id ORDER BY human_task_count DESC, task_id;"

# Check if there are any race conditions and show detailed breakdown for the first problematic task
first_duplicate_task=$(mysql_scalar_query "SELECT task_id FROM human_task WHERE process_instance_id = ${process_instance_id} GROUP BY task_id HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC, task_id LIMIT 1;" 2>/dev/null)

if [ -n "$first_duplicate_task" ]; then
  echo ""
  echo "=== 🔍 DETAILED BREAKDOWN: First problematic task GUID ==="
  echo "Task GUID: $first_duplicate_task"
  mysql_query "SELECT task_id as 'Task GUID', id as 'Human Task ID', CASE WHEN completed = 1 THEN 'true' ELSE 'false' END as 'human_task_completed', task_status, created_at_in_seconds, FROM_UNIXTIME(created_at_in_seconds) as 'Created At' FROM human_task WHERE process_instance_id = ${process_instance_id} AND task_id = '${first_duplicate_task}' ORDER BY created_at_in_seconds ASC;"
else
  echo ""
  echo "=== ✅ NO RACE CONDITION DETECTED ==="
  echo "All task GUIDs have exactly one human_task record"
fi

if [ $k6_exit_code -ne 0 ]; then
  echo ""
  echo "⚠️  k6 test failed with exit code ${k6_exit_code}"
else
  echo ""
  echo "✅ k6 test completed successfully"
fi
