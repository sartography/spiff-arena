const { port, hostname } = window.location;
let hostAndPort = hostname;
let protocol = 'https';

if (/^\d+\./.test(hostname) || hostname === 'localhost') {
  let serverPort = 7000;
  if (!Number.isNaN(Number(port))) {
    serverPort = Number(port) - 1;
  }
  hostAndPort = `${hostname}:${serverPort}`;
  protocol = 'http';
}

let url = `${protocol}://${hostAndPort}/api/v1.0`;
if (process.env.REACT_APP_BACKEND_BASE_URL) {
  url = process.env.REACT_APP_BACKEND_BASE_URL;
}

export const BACKEND_BASE_URL = url;

export const PROCESS_STATUSES = [
  'not_started',
  'user_input_required',
  'waiting',
  'complete',
  'error',
  'suspended',
  'terminated',
];

// with time: yyyy-MM-dd HH:mm:ss
export const DATE_TIME_FORMAT = 'yyyy-MM-dd HH:mm:ss';
export const TIME_FORMAT_HOURS_MINUTES = 'HH:mm';
export const DATE_FORMAT = 'yyyy-MM-dd';
export const DATE_FORMAT_CARBON = 'Y-m-d';
