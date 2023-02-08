const { port, hostname } = window.location;
let protocol = 'https';

declare global {
  interface SpiffworkflowFrontendJsenvObject {
    [key: string]: string;
  }
  interface Window {
    spiffworkflowFrontendJsenv: SpiffworkflowFrontendJsenvObject;
  }
}

let appRoutingStrategy = 'subdomain_based';
if (
  'spiffworkflowFrontendJsenv' in window &&
  'APP_ROUTING_STRATEGY' in window.spiffworkflowFrontendJsenv
) {
  appRoutingStrategy = window.spiffworkflowFrontendJsenv.APP_ROUTING_STRATEGY;
}

let hostAndPortAndPathPrefix;
if (appRoutingStrategy === 'subdomain_based') {
  hostAndPortAndPathPrefix = `api.${hostname}`;
} else if (appRoutingStrategy === 'path_based') {
  hostAndPortAndPathPrefix = `${hostname}/api`;
} else {
  throw new Error(`Invalid app routing strategy: ${appRoutingStrategy}`);
}

if (/^\d+\./.test(hostname) || hostname === 'localhost') {
  let serverPort = 7000;
  if (!Number.isNaN(Number(port))) {
    serverPort = Number(port) - 1;
  }
  hostAndPortAndPathPrefix = `${hostname}:${serverPort}`;
  protocol = 'http';
}

let url = `${protocol}://${hostAndPortAndPathPrefix}/v1.0`;

// this can only ever work locally since this is a static site.
// use spiffworkflowFrontendJsenv if you want to inject env vars
// that can be read by the static site.
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
