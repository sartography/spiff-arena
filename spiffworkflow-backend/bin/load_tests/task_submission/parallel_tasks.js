import http from "k6/http";
import { check, sleep } from "k6";
import exec from "k6/execution";

// Load API key from environment variable
const API_KEY = __ENV.SPIFF_API_KEY || __ENV.CIVI;

// Load host from environment variable, default to localhost for local development
const API_HOST = __ENV.API_HOST || "localhost:7000";

// Number of manual tasks to create and expect (configurable)
const NUM_TASKS = parseInt(__ENV.NUM_TASKS || "5");

// k6 configuration - all VUs start at the same time to create race condition
export const options = {
  vus: NUM_TASKS,
  iterations: NUM_TASKS,
  // No duration limit - just run the iterations
};

const headers = {
  "Spiffworkflow-Api-Key": API_KEY,
  "Content-Type": "application/json",
};

// Setup runs once before all VUs start
export function setup() {
  console.log(`Setting up parallel task load test for ${NUM_TASKS} tasks...`);

  const payload = JSON.stringify({ iteration_count: NUM_TASKS });

  // Step 1: Send message to start the parallel task process
  console.log(`Sending 'start-parallel-task-process' message with iteration_count: ${NUM_TASKS}...`);
  const messageResponse = http.post(
    `http://${API_HOST}/v1.0/messages/start-parallel-task-process?execution_mode=synchronous`,
    payload,
    { headers: headers },
  );

  const messageSuccess = check(messageResponse, {
    "message send status is 200": (r) => r.status === 200,
  });

  if (!messageSuccess) {
    console.error(
      `Failed to send message. Status: ${messageResponse.status}, Body: ${messageResponse.body}`,
    );
    exec.test.abort("Failed to send start message");
  }

  const messageData = messageResponse.json();

  // The response should contain process instance information
  let processInstanceId;
  if (messageData.process_instance && messageData.process_instance.id) {
    processInstanceId = messageData.process_instance.id;
  } else if (messageData.process_instance_id) {
    processInstanceId = messageData.process_instance_id;
  } else if (messageData.id) {
    processInstanceId = messageData.id;
  } else {
    console.error(`Could not find process instance ID in response: ${JSON.stringify(messageData)}`);
    exec.test.abort("Could not extract process instance ID from message response");
  }

  console.log(`Process instance started with ID: ${processInstanceId}`);
  console.log(`PROCESS_INSTANCE_ID_FOR_BASH: ${processInstanceId}`);

  // Step 2: Wait a bit for tasks to be created
  console.log("Waiting 2 seconds for manual tasks to be generated...");
  sleep(2);

  // Step 3: Query for manual tasks
  console.log("Querying for manual tasks...");
  const tasksResponse = http.get(
    `http://${API_HOST}/v1.0/tasks?process_instance_id=${processInstanceId}`,
    { headers: headers },
  );

  const tasksSuccess = check(tasksResponse, {
    "tasks query status is 200": (r) => r.status === 200,
  });

  if (!tasksSuccess) {
    console.error(
      `Failed to query tasks. Status: ${tasksResponse.status}, Body: ${tasksResponse.body}`,
    );
    exec.test.abort("Failed to query tasks");
  }

  console.log(`Tasks response body: ${tasksResponse.body}`);

  let tasksData;
  try {
    tasksData = tasksResponse.json();
  } catch (e) {
    console.error(`Failed to parse tasks response as JSON: ${e}`);
    exec.test.abort("Failed to parse tasks response");
  }

  console.log(`Parsed tasks data: ${JSON.stringify(tasksData)}`);

  // Handle different possible response structures
  let tasksList = tasksData;
  if (tasksData && tasksData.results) {
    tasksList = tasksData.results; // API might return paginated results
  } else if (tasksData && tasksData.tasks) {
    tasksList = tasksData.tasks; // API might wrap tasks in an object
  }

  if (!Array.isArray(tasksList)) {
    console.error(`Expected tasks to be an array, got: ${typeof tasksList}`);
    console.error(`Tasks data: ${JSON.stringify(tasksData)}`);
    exec.test.abort("Tasks response is not an array");
  }

  console.log(`Found ${tasksList.length} tasks`);

  if (tasksList.length < NUM_TASKS) {
    console.error(
      `Expected ${NUM_TASKS} tasks but found ${tasksList.length}. Tasks: ${JSON.stringify(tasksList)}`,
    );
    exec.test.abort(
      `Insufficient tasks: expected ${NUM_TASKS}, got ${tasksList.length}`,
    );
  }

  // Filter for manual tasks only (if needed)
  const manualTasks = tasksList.filter(
    (task) =>
      task.type === "Manual Task" ||
      task.typename === "ManualTask" ||
      task.task_type === "ManualTask",
  );

  if (manualTasks.length < NUM_TASKS) {
    console.log(
      `Found ${manualTasks.length} manual tasks out of ${tasksList.length} total tasks`,
    );
    console.log("Using all available tasks for the test...");
  }

  const tasksToUse = manualTasks.length >= NUM_TASKS ? manualTasks : tasksList;

  console.log(
    `Prepared ${tasksToUse.length} tasks for parallel submission. Starting ${NUM_TASKS} concurrent requests...`,
  );

  // Return the process instance ID and tasks so all VUs can use them
  return {
    processInstanceId: processInstanceId,
    tasks: tasksToUse.slice(0, NUM_TASKS), // Take only the number we need
  };
}

// Each VU runs this function - they all fire at roughly the same time
export default function (data) {
  const vuIndex = __VU - 1; // VU IDs start at 1, but arrays start at 0

  if (vuIndex >= data.tasks.length) {
    console.error(
      `VU ${__VU}: No task available for this VU (index ${vuIndex})`,
    );
    return;
  }

  const task = data.tasks[vuIndex];
  const taskGuid = task.id || task.guid || task.task_id;

  console.log(
    `VU ${__VU}: Submitting task ${taskGuid} for process instance ${data.processInstanceId}`,
  );

  // Submit the manual task
  const submitResponse = http.put(
    `http://${API_HOST}/v1.0/tasks/${data.processInstanceId}/${taskGuid}`,
    JSON.stringify({}), // Empty payload for now - may need task-specific data
    { headers: headers },
  );

  const success = check(submitResponse, {
    "task submission status is 200": (r) => r.status === 200,
  });

  // Always log detailed response information
  console.log(`VU ${__VU}: Task submission response for ${taskGuid}:`);
  console.log(`  Status: ${submitResponse.status}`);
  console.log(`  Headers: ${JSON.stringify(submitResponse.headers)}`);
  console.log(`  Body: ${submitResponse.body}`);

  if (success) {
    console.log(`SUCCESS: VU ${__VU}: Successfully submitted task ${taskGuid}`);
  } else {
    console.error(`FAILED: VU ${__VU}: FAILED to submit task ${taskGuid}`);
    console.error(`  Status Code: ${submitResponse.status}`);
    console.error(`  Response Body: ${submitResponse.body}`);
    console.error(
      `  Error Details: ${submitResponse.error || "No error details available"}`,
    );

    // Try to parse JSON response for more details
    try {
      const errorData = submitResponse.json();
      console.error(`  Parsed Error: ${JSON.stringify(errorData, null, 2)}`);
    } catch (e) {
      console.error(`  Could not parse response as JSON: ${e}`);
    }
  }

  // Check for specific error indicators in the response
  if (submitResponse.status >= 400) {
    console.log(
      `ERROR: VU ${__VU}: Error response - HTTP ${submitResponse.status} for task ${taskGuid}`,
    );

    // Check for ProcessInstanceIsAlreadyLockedError specifically
    if (
      submitResponse.body &&
      submitResponse.body.includes("ProcessInstanceIsAlreadyLockedError")
    ) {
      console.error(
        `LOCK ERROR DETECTED! VU ${__VU}: ProcessInstanceIsAlreadyLockedError for task ${taskGuid}`,
      );
      console.log(`LOCK_ERROR_FOR_BASH: VU_${__VU}_TASK_${taskGuid}_LOCKED`);
    }

    // Check for other race condition indicators
    if (
      submitResponse.body &&
      (submitResponse.body.includes("race") ||
        submitResponse.body.includes("conflict") ||
        submitResponse.body.includes("concurrent"))
    ) {
      console.error(
        `POTENTIAL RACE CONDITION DETECTED! VU ${__VU}: ${submitResponse.body}`,
      );
    }
  }
}
