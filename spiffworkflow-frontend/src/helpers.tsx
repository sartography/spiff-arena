import { format } from 'date-fns';
import { Buffer } from 'buffer';

import {
  DATE_TIME_FORMAT,
  DATE_FORMAT,
  TIME_FORMAT_HOURS_MINUTES,
} from './config';

export const DEFAULT_PER_PAGE = 50;
export const DEFAULT_PAGE = 1;

export const doNothing = () => {
  return undefined;
};

// https://www.30secondsofcode.org/js/s/slugify
export const slugifyString = (str: any) => {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+/g, '')
    .replace(/-+$/g, '');
};

export const HUMAN_TASK_TYPES = [
  'User Task',
  'Manual Task',
  'UserTask',
  'ManualTask',
];

export const underscorizeString = (inputString: string) => {
  return slugifyString(inputString).replace(/-/g, '_');
};

export const getKeyByValue = (
  object: any,
  value: string,
  onAttribute?: string
) => {
  return Object.keys(object).find((key) => {
    if (onAttribute) {
      return object[key][onAttribute] === value;
    }
    return object[key] === value;
  });
};

export const recursivelyChangeNullAndUndefined = (obj: any, newValue: any) => {
  if (obj === null || obj === undefined) {
    return newValue;
  }
  if (Array.isArray(obj)) {
    obj.forEach((value: any, index: number) => {
      // eslint-disable-next-line no-param-reassign
      obj[index] = recursivelyChangeNullAndUndefined(value, newValue);
    });
  } else if (typeof obj === 'object') {
    Object.entries(obj).forEach(([key, value]) => {
      // eslint-disable-next-line no-param-reassign
      obj[key] = recursivelyChangeNullAndUndefined(value, newValue);
    });
  }
  return obj;
};

export const selectKeysFromSearchParams = (obj: any, keys: string[]) => {
  const newSearchParams: { [key: string]: string } = {};
  keys.forEach((key: string) => {
    const value = obj.get(key);
    if (value) {
      newSearchParams[key] = value;
    }
  });
  return newSearchParams;
};

export const capitalizeFirstLetter = (string: any) => {
  return string.charAt(0).toUpperCase() + string.slice(1);
};

export const titleizeString = (string: any) => {
  return capitalizeFirstLetter((string || '').replaceAll('_', ' '));
};

export const convertDateToSeconds = (
  date: any,
  onChangeFunction: any = null
) => {
  let dateInSeconds = date;
  if (date !== null) {
    let dateInMilliseconds = date;
    if (typeof date.getTime === 'function') {
      dateInMilliseconds = date.getTime();
    }
    dateInSeconds = Math.floor(dateInMilliseconds / 1000);
  }

  if (onChangeFunction) {
    onChangeFunction(dateInSeconds);
  } else {
    return dateInSeconds;
  }

  return null;
};

export const convertDateObjectToFormattedString = (dateObject: Date) => {
  if (dateObject) {
    return format(dateObject, DATE_FORMAT);
  }
  return null;
};

export const dateStringToYMDFormat = (dateString: string) => {
  if (dateString && dateString.match(/^\d{2}-\d{2}-\d{4}$/)) {
    if (DATE_FORMAT.startsWith('dd')) {
      const d = dateString.split('-');
      return `${d[2]}-${d[1]}-${d[0]}`;
    }
    if (DATE_FORMAT.startsWith('MM')) {
      const d = dateString.split('-');
      return `${d[2]}-${d[0]}-${d[1]}`;
    }
  }
  return dateString;
};

export const convertDateAndTimeStringsToDate = (
  dateString: string,
  timeString: string
) => {
  if (dateString && timeString) {
    return new Date(`${dateStringToYMDFormat(dateString)}T${timeString}`);
  }
  return null;
};

export const convertDateAndTimeStringsToSeconds = (
  dateString: string,
  timeString: string
) => {
  const dateObject = convertDateAndTimeStringsToDate(dateString, timeString);
  if (dateObject) {
    return convertDateToSeconds(dateObject);
  }
  return null;
};

export const convertStringToDate = (dateString: string) => {
  return convertDateAndTimeStringsToDate(dateString, '00:10:00');
};

export const ymdDateStringToConfiguredFormat = (dateString: string) => {
  const dateObject = convertStringToDate(dateString);
  if (dateObject) {
    return convertDateObjectToFormattedString(dateObject);
  }
  return null;
};

export const convertSecondsToDateObject = (seconds: number) => {
  if (seconds) {
    return new Date(seconds * 1000);
  }
  return null;
};

export const convertSecondsToFormattedDateTime = (seconds: number) => {
  const dateObject = convertSecondsToDateObject(seconds);
  if (dateObject) {
    return format(dateObject, DATE_TIME_FORMAT);
  }
  return null;
};

export const convertDateObjectToFormattedHoursMinutes = (dateObject: Date) => {
  if (dateObject) {
    return format(dateObject, TIME_FORMAT_HOURS_MINUTES);
  }
  return null;
};

export const convertSecondsToFormattedTimeHoursMinutes = (seconds: number) => {
  const dateObject = convertSecondsToDateObject(seconds);
  if (dateObject) {
    return convertDateObjectToFormattedHoursMinutes(dateObject);
  }
  return null;
};

export const convertSecondsToFormattedDateString = (seconds: number) => {
  const dateObject = convertSecondsToDateObject(seconds);
  if (dateObject) {
    return convertDateObjectToFormattedString(dateObject);
  }
  return null;
};

export const convertDateStringToSeconds = (dateString: string) => {
  const dateObject = convertStringToDate(dateString);
  if (dateObject) {
    return convertDateToSeconds(dateObject);
  }
  return null;
};

export const objectIsEmpty = (obj: object) => {
  return Object.keys(obj).length === 0;
};

export const getPageInfoFromSearchParams = (
  searchParams: any,
  defaultPerPage: string | number = DEFAULT_PER_PAGE,
  defaultPage: string | number = DEFAULT_PAGE,
  paginationQueryParamPrefix: string | null = null
) => {
  const paginationQueryParamPrefixToUse = paginationQueryParamPrefix
    ? `${paginationQueryParamPrefix}_`
    : '';
  const page = parseInt(
    searchParams.get(`${paginationQueryParamPrefixToUse}page`) ||
      defaultPage.toString(),
    10
  );
  const perPage = parseInt(
    searchParams.get(`${paginationQueryParamPrefixToUse}per_page`) ||
      defaultPerPage.toString(),
    10
  );

  return { page, perPage };
};

// https://stackoverflow.com/a/1349426/6090676
export const makeid = (length: number) => {
  let result = '';
  const characters = 'abcdefghijklmnopqrstuvwxyz0123456789';
  const charactersLength = characters.length;
  for (let i = 0; i < length; i += 1) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
};

export const getProcessModelFullIdentifierFromSearchParams = (
  searchParams: any
) => {
  let processModelFullIdentifier = null;
  if (searchParams.get('process_model_identifier')) {
    processModelFullIdentifier = `${searchParams.get(
      'process_model_identifier'
    )}`;
  }
  return processModelFullIdentifier;
};

// https://stackoverflow.com/a/71352046/6090676
export const truncateString = (text: string, len: number) => {
  if (text.length > len && text.length > 0) {
    return `${text.split('').slice(0, len).join('')} ...`;
  }
  return text;
};

// Because of limitations in the way openapi defines parameters, we have to modify process models ids
// which are basically paths to the models
export const modifyProcessIdentifierForPathParam = (path: string) => {
  return path.replace(/\//g, ':') || '';
};

export const unModifyProcessIdentifierForPathParam = (path: string) => {
  return path.replace(/:/g, '/') || '';
};

export const getGroupFromModifiedModelId = (modifiedId: string) => {
  const finalSplitIndex = modifiedId.lastIndexOf(':');
  return modifiedId.slice(0, finalSplitIndex);
};

export const splitProcessModelId = (processModelId: string) => {
  return processModelId.split('/');
};

export const refreshAtInterval = (
  interval: number,
  timeout: number,
  periodicFunction: Function,
  cleanupFunction?: Function
) => {
  const intervalRef = setInterval(() => periodicFunction(), interval * 1000);
  const timeoutRef = setTimeout(() => {
    clearInterval(intervalRef);
    if (cleanupFunction) {
      cleanupFunction();
    }
  }, timeout * 1000);
  return () => {
    clearInterval(intervalRef);
    if (cleanupFunction) {
      cleanupFunction();
    }
    clearTimeout(timeoutRef);
  };
};

// bpmn:SubProcess shape elements do not have children
// but their moddle elements / businessOjects have flowElements
// that can include the moddleElement of the subprocesses
const getChildProcessesFromModdleElement = (bpmnModdleElement: any) => {
  let elements: string[] = [];
  bpmnModdleElement.flowElements.forEach((c: any) => {
    if (c.$type === 'bpmn:SubProcess') {
      elements.push(c.id);
      elements = [...elements, ...getChildProcessesFromModdleElement(c)];
    }
  });
  return elements;
};

const getChildProcesses = (bpmnElement: any) => {
  let elements: string[] = [];
  bpmnElement.children.forEach((c: any) => {
    if (c.type === 'bpmn:Participant') {
      if (c.businessObject.processRef) {
        elements.push(c.businessObject.processRef.id);
      }
      elements = [...elements, ...getChildProcesses(c)];
    } else if (c.type === 'bpmn:SubProcess') {
      elements.push(c.id);
      elements = [
        ...elements,
        ...getChildProcessesFromModdleElement(c.businessObject),
      ];
    }
  });
  return elements;
};

export const getBpmnProcessIdentifiers = (rootBpmnElement: any) => {
  const childProcesses = getChildProcesses(rootBpmnElement);
  childProcesses.push(rootBpmnElement.businessObject.id);
  return childProcesses;
};

export const isInteger = (str: string | number) => {
  return /^\d+$/.test(str.toString());
};

export const encodeBase64 = (data: string) => {
  return Buffer.from(data).toString('base64');
};

export const decodeBase64 = (data: string) => {
  return Buffer.from(data, 'base64').toString('ascii');
};

const MINUTES_IN_HOUR = 60;
const SECONDS_IN_MINUTE = 60;
const SECONDS_IN_HOUR = MINUTES_IN_HOUR * SECONDS_IN_MINUTE;
const FOUR_HOURS_IN_SECONDS = SECONDS_IN_HOUR * 4;

export const REFRESH_INTERVAL_SECONDS = 5;
export const REFRESH_TIMEOUT_SECONDS = FOUR_HOURS_IN_SECONDS;
