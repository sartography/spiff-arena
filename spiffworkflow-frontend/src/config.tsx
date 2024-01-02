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

let spiffEnvironment = '';
let appRoutingStrategy = 'subdomain_based';
let backendBaseUrl = null;
let documentationUrl = null;
if ('spiffworkflowFrontendJsenv' in window) {
  if ('APP_ROUTING_STRATEGY' in window.spiffworkflowFrontendJsenv) {
    appRoutingStrategy = window.spiffworkflowFrontendJsenv.APP_ROUTING_STRATEGY;
  }
  if ('ENVIRONMENT_IDENTIFIER' in window.spiffworkflowFrontendJsenv) {
    spiffEnvironment = window.spiffworkflowFrontendJsenv.ENVIRONMENT_IDENTIFIER;
  }
  if ('BACKEND_BASE_URL' in window.spiffworkflowFrontendJsenv) {
    backendBaseUrl = window.spiffworkflowFrontendJsenv.BACKEND_BASE_URL;
  }
  if ('DOCUMENTATION_URL' in window.spiffworkflowFrontendJsenv) {
    documentationUrl = window.spiffworkflowFrontendJsenv.DOCUMENTATION_URL;
  }
}

if (!backendBaseUrl) {
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

    if (spiffEnvironment === '') {
      // using destructuring on an array where we only want the first element
      // seems super confusing for non-javascript devs to read so let's NOT do that.
      // eslint-disable-next-line prefer-destructuring
      spiffEnvironment = hostname.split('.')[0];
    }
  }

  backendBaseUrl = `${protocol}://${hostAndPortAndPathPrefix}/v1.0`;

  // this can only ever work locally since this is a static site.
  // use spiffworkflowFrontendJsenv if you want to inject env vars
  // that can be read by the static site.
  if (process.env.REACT_APP_BACKEND_BASE_URL) {
    backendBaseUrl = process.env.REACT_APP_BACKEND_BASE_URL;
  }
}

if (!backendBaseUrl.endsWith('/v1.0')) {
  backendBaseUrl += '/v1.0';
}

export const BACKEND_BASE_URL = backendBaseUrl;
export const DOCUMENTATION_URL = documentationUrl;

export const PROCESS_STATUSES = [
  'complete',
  'error',
  'not_started',
  'running',
  'suspended',
  'terminated',
  'user_input_required',
  'waiting',
];

// with time: yyyy-MM-dd HH:mm:ss
let generalDateFormat = 'yyyy-MM-dd';
if (
  'spiffworkflowFrontendJsenv' in window &&
  'DATE_FORMAT' in window.spiffworkflowFrontendJsenv
) {
  generalDateFormat = window.spiffworkflowFrontendJsenv.DATE_FORMAT;
}

const splitDateFormat = generalDateFormat.split('-');
const supportedDateFormatTypes = ['yyyy', 'MM', 'MMM', 'MMMM', 'dd'];
const unsupportedFormatTypes = splitDateFormat.filter(
  (x) => !supportedDateFormatTypes.includes(x)
);
if (unsupportedFormatTypes.length > 0) {
  throw new Error(
    `Given SPIFFWORKFLOW_FRONTEND_RUNTIME_CONFIG_DATE_FORMAT is not supported. Given: ${generalDateFormat} with invalid options: ${unsupportedFormatTypes.join(
      ', '
    )}. Valid options are: ${supportedDateFormatTypes.join(', ')}`
  );
}
const carbonDateFormat = generalDateFormat
  .replace(/\byyyy\b/, 'Y')
  .replace(/\bMM\b/, 'm')
  .replace(/\bMMM\b/, 'M')
  .replace(/\bMMMM\b/, 'F')
  .replace(/\bdd\b/, 'd');
export const DATE_TIME_FORMAT = `${generalDateFormat} HH:mm:ss`;
export const TIME_FORMAT_HOURS_MINUTES = 'HH:mm';
export const DATE_FORMAT = generalDateFormat;
export const DATE_FORMAT_CARBON = carbonDateFormat;
export const DATE_FORMAT_FOR_DISPLAY = generalDateFormat.toLowerCase();
export const DATE_RANGE_DELIMITER = ':::';

export const SPIFF_ENVIRONMENT = spiffEnvironment;
