import { Buffer } from 'buffer';

import { createRoot } from 'react-dom/client';
import { flushSync } from 'react-dom';
import { ReactElement } from 'react';
import { ElementForArray, ProcessInstance } from './interfaces';

export const DEFAULT_PER_PAGE = 50;
export const DEFAULT_PAGE = 1;

export const doNothing = () => {
  return undefined;
};

export const matchNumberRegex = /^[0-9,.-]*$/;

// https://www.30secondsofcode.org/js/s/slugify
export const slugifyString = (str: string) => {
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
  'Task',

  // HumanTaskModel.task_type is sometimes set to this and it is the same as "Task"
  'NoneTask',
];

export const MULTI_INSTANCE_TASK_TYPES = [
  'ParallelMultiInstanceTask',
  'SequentialMultiInstanceTask',
];

export const LOOP_TASK_TYPES = ['StandardLoopTask'];

export const underscorizeString = (inputString: string) => {
  return slugifyString(inputString).replace(/-/g, '_');
};

export const getKeyByValue = (
  object: any,
  value: string,
  onAttribute?: string,
) => {
  return Object.keys(object).find((key) => {
    if (onAttribute) {
      return object[key][onAttribute] === value;
    }
    return object[key] === value;
  });
};

// NOTE: rjsf sets blanks values to undefined and JSON.stringify removes keys with undefined values
// so we convert undefined values to null recursively so that we can unset values in form fields
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

export const objectIsEmpty = (obj: object) => {
  return Object.keys(obj).length === 0;
};

export const getPageInfoFromSearchParams = (
  searchParams: any,
  defaultPerPage: string | number = DEFAULT_PER_PAGE,
  defaultPage: string | number = DEFAULT_PAGE,
  paginationQueryParamPrefix: string | null = null,
) => {
  const paginationQueryParamPrefixToUse = paginationQueryParamPrefix
    ? `${paginationQueryParamPrefix}_`
    : '';
  const page = parseInt(
    searchParams.get(`${paginationQueryParamPrefixToUse}page`) ||
      defaultPage.toString(),
    10,
  );
  const perPage = parseInt(
    searchParams.get(`${paginationQueryParamPrefixToUse}per_page`) ||
      defaultPerPage.toString(),
    10,
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
  searchParams: any,
) => {
  let processModelFullIdentifier = null;
  if (searchParams.get('process_model_identifier')) {
    processModelFullIdentifier = `${searchParams.get(
      'process_model_identifier',
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

export const pathFromFullUrl = (fullUrl: string) => {
  const parsedURL = new URL(fullUrl);
  return parsedURL.pathname;
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
  cleanupFunction?: Function,
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

export const setPageTitle = (items: Array<string>) => {
  document.title = ['SpiffWorkflow'].concat(items).join(' - ');
};

// calling it isANumber to avoid confusion with other libraries
// that have isNumber methods
export const isANumber = (str: string | number | null) => {
  if (str === undefined || str === null) {
    return false;
  }
  return /^\d+(\.\d+)?$/.test(str.toString());
};

export const encodeBase64 = (data: string) => {
  return Buffer.from(data).toString('base64');
};

export const decodeBase64 = (data: string) => {
  return Buffer.from(data, 'base64').toString('ascii');
};

export const getLastMilestoneFromProcessInstance = (
  processInstance: ProcessInstance,
  value: any,
) => {
  let valueToUse = value;
  if (!valueToUse) {
    if (processInstance.status === 'not_started') {
      valueToUse = 'Created';
    } else if (
      ['complete', 'error', 'terminated'].includes(processInstance.status)
    ) {
      valueToUse = 'Completed';
    } else {
      valueToUse = 'Started';
    }
  }
  let truncatedValue = valueToUse;
  const milestoneLengthLimit = 20;
  if (truncatedValue.length > milestoneLengthLimit) {
    truncatedValue = `${truncatedValue.substring(
      0,
      milestoneLengthLimit - 3,
    )}...`;
  }
  return [valueToUse, truncatedValue];
};

export const parseTaskShowUrl = (url: string) => {
  const path = pathFromFullUrl(url);

  // expected url pattern:
  // /tasks/[process_instance_id]/[task_guid]
  return path.match(
    /^\/tasks\/(\d+)\/([0-9a-z]{8}-([0-9a-z]{4}-){3}[0-9a-z]{12})$/,
  );
};

// https://stackoverflow.com/a/15855457/6090676
export const isURL = (str: string) => {
  const urlRegex =
    // eslint-disable-next-line max-len
    /^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,}))?)(?::\d{2,5})?(?:[/?#]\S*)?$/i;
  return urlRegex.test(str);
};

// this will help maintain order when using an array of elements.
// React needs to have a key for each component to ensure correct elements are added
// and removed when that array is changed.
// https://stackoverflow.com/questions/46735483/error-do-not-use-array-index-in-keys/46735689#46735689
export const renderElementsForArray = (elements: ElementForArray[]) => {
  return elements.map((element: any) => (
    <div key={element.key}>{element.component}</div>
  ));
};

export const convertSvgElementToHtmlString = (svgElement: ReactElement) => {
  // vite with svgr imports svg files as react components but we need the html string value at times
  // so this converts the component to html string
  const div = document.createElement('div');
  const root = createRoot(div);
  flushSync(() => {
    root.render(svgElement);
  });
  return div.innerHTML;
};
