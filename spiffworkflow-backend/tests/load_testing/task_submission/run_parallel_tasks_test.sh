#!/usr/bin/env bash

set -eo pipefail

script_dir="$(
  cd -- "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

# Check if SPIFF_API_KEY environment variable is set
if [ -z "${SPIFF_API_KEY:-}" ]; then
  echo "Error: SPIFF_API_KEY environment variable is not set"
  echo "Please set it with: export SPIFF_API_KEY=your_api_key"
  exit 1
fi

# Default values
NUM_TASKS=${NUM_TASKS:-5}
API_HOST=${API_HOST:-host.docker.internal:7000}

echo "=========================================="
echo "Parallel Manual Tasks Load Test"
echo "=========================================="
echo "Number of tasks to create: ${NUM_TASKS}"
echo "Number of concurrent VUs: ${NUM_TASKS}"
echo "API Host: ${API_HOST}"
echo "Starting test..."
echo ""

# Run k6 test and capture exit code and output
set +e
k6_output=$(docker run --rm --add-host=host.docker.internal:host-gateway -i grafana/k6 \
  -e SPIFF_API_KEY="$SPIFF_API_KEY" \
  -e API_HOST="$API_HOST" \
  -e NUM_TASKS="$NUM_TASKS" \
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

# Check for duplicate human task records by task GUID (the race condition we're looking for)
echo "=== 🔍 RACE CONDITION CHECK: Multiple human_task records per task GUID ==="
mysql -uroot spiffworkflow_backend_local_development -e "SELECT task_id, COUNT(*) as human_task_count, GROUP_CONCAT(id ORDER BY id) as human_task_record_ids, GROUP_CONCAT(created_at_in_seconds ORDER BY id) as created_timestamps FROM human_task WHERE process_instance_id = ${process_instance_id} GROUP BY task_id HAVING COUNT(*) > 1 ORDER BY human_task_count DESC;"

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
mysql -uroot spiffworkflow_backend_local_development -e "SELECT id, task_id, process_instance_id, task_name, task_title, completed, created_at_in_seconds, FROM_UNIXTIME(created_at_in_seconds) as created_at FROM human_task WHERE process_instance_id = ${process_instance_id} ORDER BY task_id, created_at_in_seconds ASC;"

echo ""
echo "=== Summary: Human task counts by task GUID ==="
mysql -uroot spiffworkflow_backend_local_development -e "SELECT task_id, COUNT(*) as human_task_count, GROUP_CONCAT(CASE WHEN completed = 1 THEN 'COMPLETED' ELSE 'PENDING' END) as completion_status, CASE WHEN COUNT(*) > 1 THEN 'DUPLICATE - RACE CONDITION!' ELSE 'Normal' END as status FROM human_task WHERE process_instance_id = ${process_instance_id} GROUP BY task_id ORDER BY human_task_count DESC, task_id;"

# Check if there are any race conditions and show detailed breakdown for the first problematic task
first_duplicate_task=$(mysql -uroot spiffworkflow_backend_local_development -s -e "SELECT task_id FROM human_task WHERE process_instance_id = ${process_instance_id} GROUP BY task_id HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC, task_id LIMIT 1;" 2>/dev/null)

if [ -n "$first_duplicate_task" ]; then
  echo ""
  echo "=== 🔍 DETAILED BREAKDOWN: First problematic task GUID ==="
  echo "Task GUID: $first_duplicate_task"
  mysql -uroot spiffworkflow_backend_local_development -e "SELECT task_id as 'Task GUID', id as 'Human Task ID', CASE WHEN completed = 1 THEN 'true' ELSE 'false' END as 'human_task_completed', task_status, created_at_in_seconds, FROM_UNIXTIME(created_at_in_seconds) as 'Created At' FROM human_task WHERE process_instance_id = ${process_instance_id} AND task_id = '${first_duplicate_task}' ORDER BY created_at_in_seconds ASC;"
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
