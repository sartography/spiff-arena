import { format } from 'date-fns';
import { DATE_FORMAT } from './config';
import {
  DEFAULT_PER_PAGE,
  DEFAULT_PAGE,
} from './components/PaginationForTable';

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

export const capitalizeFirstLetter = (string: any) => {
  return string.charAt(0).toUpperCase() + string.slice(1);
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

export const convertStringToDate = (dateString: string) => {
  if (dateString) {
    return new Date(dateString);
  }
  return null;
};

export const convertSecondsToFormattedDate = (seconds: number) => {
  if (seconds) {
    const dateObject = new Date(seconds * 1000);
    return format(dateObject, DATE_FORMAT);
  }
  return null;
};

export const convertDateStringToSeconds = (dateString: string) => {
  const dateObject = convertStringToDate(dateString);
  return convertDateToSeconds(dateObject);
};

export const objectIsEmpty = (obj: object) => {
  return Object.keys(obj).length === 0;
};

export const getPageInfoFromSearchParams = (
  searchParams: any,
  defaultPerPage: string | number = DEFAULT_PER_PAGE,
  defaultPage: string | number = DEFAULT_PAGE
) => {
  const page = parseInt(searchParams.get('page') || defaultPage.toString(), 10);
  const perPage = parseInt(
    searchParams.get('per_page') || defaultPerPage.toString(),
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
  if (
    searchParams.get('process_model_identifier') &&
    searchParams.get('process_group_identifier')
  ) {
    processModelFullIdentifier = `${searchParams.get(
      'process_group_identifier'
    )}/${searchParams.get('process_model_identifier')}`;
  }
  return processModelFullIdentifier;
};

// https://stackoverflow.com/a/71352046/6090676
export const truncateString = (text: string, len: number) => {
  if (text.length > len && text.length > 0) {
    return `${text.split(' ').slice(0, len).join(' ')} ...`;
  }
  return text;
};

// Because of limitations in the way openapi defines parameters, we have to modify process models ids
// which are basically paths to the models
export const modifyProcessModelPath = (path: String) => {
  return path.replace('/', ':') || '';
};

export const unModifyProcessModelPath = (path: String) => {
  return path.replace(':', '/') || '';
};

export const getGroupFromModifiedModelId = (modifiedId: String) => {
  const finalSplitIndex = modifiedId.lastIndexOf(':');
  return modifiedId.slice(0, finalSplitIndex);
};

export const splitProcessModelId = (processModelId: String) => {
  return processModelId.split('/');
};
