const host = window.location.hostname;
let hostAndPort = `api.${host}`;
let protocol = 'https';
if (/^\d+\./.test(host) || host === 'localhost') {
  hostAndPort = `${host}:7000`;
  protocol = 'http';
}
export const BACKEND_BASE_URL = `${protocol}://${hostAndPort}/v1.0`;

export const PROCESS_STATUSES = [
  'not_started',
  'user_input_required',
  'waiting',
  'complete',
  'faulted',
  'suspended',
];

// with time: yyyy-MM-dd HH:mm:ss
export const DATE_TIME_FORMAT = 'yyyy-MM-dd HH:mm:ss';
export const DATE_FORMAT = 'yyyy-MM-dd';
export const DATE_FORMAT_CARBON = 'Y-m-d';
