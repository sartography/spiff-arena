import http from "k6/http";
import { check, sleep } from "k6";
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.4.0/index.js";
import exec from "k6/execution";

// Load API key from environment variable
const API_KEY = __ENV.SPIFF_API_KEY || __ENV.CIVI;

// Load host from environment variable, default to localhost for local development
const API_HOST = __ENV.API_HOST || "localhost:7000";

// Number of concurrent requests to hammer the process instance with
const CONCURRENT_REQUESTS = parseInt(__ENV.CONCURRENT_REQUESTS || "2");

// k6 configuration - all VUs start at the same time to create race condition
export const options = {
  vus: CONCURRENT_REQUESTS,
  iterations: CONCURRENT_REQUESTS,
  // No duration limit - just run the iterations
};

const headers = {
  "Spiffworkflow-Api-Key": API_KEY,
  "Content-Type": "application/json",
};

// Setup runs once before all VUs start
export function setup() {
  const uuid = uuidv4();
  console.log(`Using correlation key (UUID): ${uuid}`);

  const payload = JSON.stringify({ x: uuid });

  // Send the first message to create/start the process instance
  console.log("Sending message 'one' to start process instance...");
  const response = http.post(
    `http://${API_HOST}/v1.0/messages/one?execution_mode=synchronous`,
    payload,
    { headers: headers },
  );

  const success = check(response, {
    "message/one status is 200": (r) => r.status === 200,
  });

  if (!success) {
    console.error(
      `Failed to send message 'one'. Status: ${response.status}, Body: ${response.body}`,
    );
  } else {
    console.log("Message 'one' sent successfully");
  }

  // Wait 1 second for the process instance to settle
  console.log("Waiting 1 second for process instance to settle...");
  sleep(1);

  console.log(
    `Now hammering with ${CONCURRENT_REQUESTS} concurrent 'two' messages...`,
  );

  // Return the UUID so all VUs can use it
  return { uuid: uuid };
}

// Each VU runs this function - they all fire at roughly the same time
export default function (data) {
  const payload = JSON.stringify({ x: data.uuid });

  // All VUs send message "two" with the same correlation key simultaneously
  const response = http.post(
    `http://${API_HOST}/v1.0/messages/two?execution_mode=synchronous`,
    payload,
    { headers: headers },
  );

  check(response, {
    "message/two status is 200": (r) => r.status === 200,
  });

  // Check if this is the race condition we're looking for
  if (
    response.body &&
    response.body.includes("This process is not waiting for two")
  ) {
    console.error(
      `🔴 RACE CONDITION REPRODUCED! VU ${__VU}: Found "This process is not waiting for two" in response`,
    );
    console.error(`Response status: ${response.status}`);
    console.error(`Response body: ${response.body}`);
    // Abort the test immediately with a specific exit code
    exec.test.abort(
      "Race condition reproduced - process not waiting for message",
    );
  }

  if (response.status !== 200) {
    console.error(
      `VU ${__VU}: message/two failed. Status: ${response.status}, Body: ${response.body}`,
    );
  } else {
    console.log(`VU ${__VU}: message/two succeeded`);
  }
}
