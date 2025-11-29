import http from "k6/http";
import { check } from "k6";
import { uuidv4 } from "https://jslib.k6.io/k6-utils/1.4.0/index.js";

// Load API key from environment variable
const API_KEY = __ENV.CIVI;

// Load host from environment variable, default to localhost for local development
const API_HOST = __ENV.API_HOST || "localhost:7000";
// const API_HOST = __ENV.API_HOST || "host.docker.internal:7000";

// k6 configuration
export const options = {
  vus: 10, // 10 virtual users (5 iterations * 2 concurrent requests)
  iterations: 10, // Total 10 requests (5 pairs)
  duration: "30s", // Maximum duration
};

export default function () {
  const uuid = uuidv4();

  const headers = {
    "Spiffworkflow-Api-Key": API_KEY,
    "Content-Type": "application/json",
  };

  const payload = JSON.stringify({ x: uuid });

  // Make requests sequentially - first message/one, then message/two
  const response1 = http.post(
    `http://${API_HOST}/v1.0/messages/one?execution_mode=synchronous`,
    payload,
    { headers: headers }
  );

  // Check first response
  check(response1, {
    "message/one status is 200": (r) => r.status === 200,
  });

  // Fire second request only after first completes
  const response2 = http.post(
    `http://${API_HOST}/v1.0/messages/two?execution_mode=synchronous`,
    payload,
    { headers: headers }
  );

  // Check second response
  check(response2, {
    "message/two status is 200": (r) => r.status === 200,
  });
}
