declare const window: Window & typeof globalThis;

import { TaskMetadata, TaskMetadataArraySchema } from './interfaces';

const { port, hostname } = window.location;
let protocol = 'https';

const CONFIGURATION_ERRORS: string[] = [];

declare global {
  interface SpiffworkflowFrontendJsenvObject {
    [key: string]: string;
  }
  interface Window {
    spiffworkflowFrontendJsenv: SpiffworkflowFrontendJsenvObject;
  }
}

// Helper function to get config value from either runtime config or Vite env
function getConfigValue(key: string): string | null {
  if ('spiffworkflowFrontendJsenv' in window) {
    if (key in window.spiffworkflowFrontendJsenv) {
      return window.spiffworkflowFrontendJsenv[key];
    }
  }

  if (import.meta.env) {
    const viteKey = `VITE_${key}`;
    if (viteKey in import.meta.env) {
      return import.meta.env[viteKey];
    }
  }

  return null;
}

let darkModeEnabled = getConfigValue('DARK_MODE_ENABLED');
if (darkModeEnabled === null) {
  darkModeEnabled = 'true';
}

const DARK_MODE_ENABLED = !!(
  darkModeEnabled && darkModeEnabled.toLowerCase() === 'true'
);

let appRoutingStrategy = getConfigValue('APP_ROUTING_STRATEGY');
if (appRoutingStrategy === null) {
  appRoutingStrategy = 'subdomain_based';
}

let spiffEnvironment = getConfigValue('ENVIRONMENT_IDENTIFIER') || '';

let backendBaseUrl = getConfigValue('BACKEND_BASE_URL');

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

      spiffEnvironment = hostname.split('.')[0];
    }
  }

  backendBaseUrl = `${protocol}://${hostAndPortAndPathPrefix}/v1.0`;
}

if (!backendBaseUrl.endsWith('/v1.0')) {
  backendBaseUrl += '/v1.0';
}

const documentationUrl = getConfigValue('DOCUMENTATION_URL');

const taskMetadataJson = getConfigValue('TASK_METADATA');
let taskMetadata: TaskMetadata | null = null;
if (taskMetadataJson) {
  try {
    taskMetadata = JSON.parse(taskMetadataJson);
    // this will validate the object
    TaskMetadataArraySchema.parse(taskMetadata);
  } catch (error: any) {
    CONFIGURATION_ERRORS.push(
      `Unable to parse configuration 'TASK_METADATA'. Error was ${error.message}`,
    );
  }
}
const TASK_METADATA = taskMetadata;

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

const MESSAGE_STATUSES = [
  'ready',
  'running',
  'completed',
  'failed',
  'cancelled',
];

const MESSAGE_TYPES = ['send', 'receive'];

// with time: yyyy-MM-dd HH:mm:ss
let generalDateFormat = getConfigValue('DATE_FORMAT');
if (generalDateFormat === null) {
  generalDateFormat = 'yyyy-MM-dd';
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
  BACKEND_BASE_URL,
  CONFIGURATION_ERRORS,
  DARK_MODE_ENABLED,
  DATE_FORMAT,
  DATE_FORMAT_CARBON,
  DATE_FORMAT_FOR_DISPLAY,
  DATE_RANGE_DELIMITER,
  DATE_TIME_FORMAT,
  DOCUMENTATION_URL,
  MESSAGE_STATUSES,
  MESSAGE_TYPES,
  PROCESS_STATUSES,
  SPIFF_ENVIRONMENT,
  TASK_METADATA,
  TIME_FORMAT_HOURS_MINUTES,
};
