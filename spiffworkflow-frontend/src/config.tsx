declare const window: Window & typeof globalThis;

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
}

if (!backendBaseUrl.endsWith('/v1.0')) {
  backendBaseUrl += '/v1.0';
}

const BACKEND_BASE_URL = backendBaseUrl;
const DOCUMENTATION_URL = documentationUrl;

const PROCESS_STATUSES = [
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
// let generalDateFormat = 'dd-MMM-yyyy';
if (
  'spiffworkflowFrontendJsenv' in window &&
  'DATE_FORMAT' in window.spiffworkflowFrontendJsenv
) {
  generalDateFormat = window.spiffworkflowFrontendJsenv.DATE_FORMAT;
}

const splitDateFormat = generalDateFormat.split('-');

// https://date-fns.org/v3.0.6/docs/format
const supportedDateFormatTypes = {
  yyyy: '2024',
  MM: '01',
  MMM: 'Jan',
  MMMM: 'January',
  dd: '01',
};
const unsupportedFormatTypes = splitDateFormat.filter(
  (x) => !Object.keys(supportedDateFormatTypes).includes(x),
);
const formattedSupportedDateTypes: string[] = [];
Object.entries(supportedDateFormatTypes).forEach(([key, value]) => {
  formattedSupportedDateTypes.push(`${key}: ${value}`);
});
if (unsupportedFormatTypes.length > 0) {
  throw new Error(
    `Given SPIFFWORKFLOW_FRONTEND_RUNTIME_CONFIG_DATE_FORMAT is not supported. Given: ${generalDateFormat} with invalid options: ${unsupportedFormatTypes.join(
      ', ',
    )}. Valid options are: ${formattedSupportedDateTypes.join(', ')}`,
  );
}
const carbonDateFormat = generalDateFormat
  .replace(/\byyyy\b/, 'Y')
  .replace(/\bMM\b/, 'm')
  .replace(/\bMMM\b/, 'M')
  .replace(/\bMMMM\b/, 'F')
  .replace(/\bdd\b/, 'd');
const DATE_TIME_FORMAT = `${generalDateFormat} HH:mm:ss`;
const TIME_FORMAT_HOURS_MINUTES = 'HH:mm';
const DATE_FORMAT = generalDateFormat;
const DATE_FORMAT_CARBON = carbonDateFormat;
const DATE_FORMAT_FOR_DISPLAY = generalDateFormat.toLowerCase();
const DATE_RANGE_DELIMITER = ':::';

const SPIFF_ENVIRONMENT = spiffEnvironment;
export {
  DATE_TIME_FORMAT,
  TIME_FORMAT_HOURS_MINUTES,
  DATE_FORMAT,
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
  DATE_RANGE_DELIMITER,
  BACKEND_BASE_URL,
  DOCUMENTATION_URL,
  PROCESS_STATUSES,
  SPIFF_ENVIRONMENT,
};
