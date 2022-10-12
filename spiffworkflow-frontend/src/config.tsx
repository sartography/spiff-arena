const host = window.location.hostname;
export const HOST_AND_PORT = `${host}:7000`;

export const BACKEND_BASE_URL = `http://${HOST_AND_PORT}/v1.0`;

export const PROCESS_STATUSES = [
  'not_started',
  'user_input_required',
  'waiting',
  'complete',
  'faulted',
  'suspended',
];

export const DATE_FORMAT = 'yyyy-MM-dd HH:mm:ss';
