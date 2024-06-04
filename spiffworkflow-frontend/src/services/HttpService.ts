/* eslint-disable max-classes-per-file */
import { BACKEND_BASE_URL } from '../config';
import { objectIsEmpty } from '../helpers';
import UserService from './UserService';

const HttpMethods = {
  GET: 'GET',
  POST: 'POST',
  DELETE: 'DELETE',
};

export const getBasicHeaders = (): Record<string, string> => {
  if (UserService.isLoggedIn()) {
    return {
      Authorization: `Bearer ${UserService.getAccessToken()}`,
      'SpiffWorkflow-Authentication-Identifier':
        UserService.getAuthenticationIdentifier() || 'default',
    };
  }
  return {};
};

type backendCallProps = {
  path: string;
  successCallback: Function;
  failureCallback?: Function;
  onUnauthorized?: Function;
  httpMethod?: string;
  extraHeaders?: object;
  postBody?: any;
};

export class UnauthenticatedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnauthenticatedError';
  }
}

export class UnexpectedResponseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnexpectedResponseError';
  }
}

const messageForHttpError = (statusCode: number, statusText: string) => {
  let errorMessage = `HTTP Error ${statusCode}`;
  if (statusText) {
    errorMessage += `: ${statusText}`;
  } else {
    let httpTextForCode = '';
    switch (statusCode) {
      case 400:
        httpTextForCode = 'Bad Request';
        break;
      case 401:
        httpTextForCode = 'Unauthorized';
        break;
      case 403:
        httpTextForCode = 'Forbidden';
        break;
      case 404:
        httpTextForCode = 'Not Found';
        break;
      case 413:
        httpTextForCode = 'Payload Too Large';
        break;
      case 500:
        httpTextForCode = 'Internal Server Error';
        break;
      case 502:
        httpTextForCode = 'Bad Gateway';
        break;
      case 503:
        httpTextForCode = 'Service Unavailable';
        break;
      default:
        break;
    }
    if (httpTextForCode) {
      errorMessage += `: ${httpTextForCode}`;
    }
  }
  return errorMessage;
};

const makeCallToBackend = ({
  path,
  successCallback,
  failureCallback,
  onUnauthorized,
  httpMethod = 'GET',
  extraHeaders = {},
  postBody = {},
}: // eslint-disable-next-line sonarjs/cognitive-complexity
backendCallProps) => {
  const headers = getBasicHeaders();

  if (!objectIsEmpty(extraHeaders)) {
    Object.assign(headers, extraHeaders);
  }

  const httpArgs = {};

  if (postBody instanceof FormData) {
    Object.assign(httpArgs, { body: postBody });
  } else if (typeof postBody === 'object') {
    if (!objectIsEmpty(postBody)) {
      // NOTE: stringify strips out keys with value undefined
      Object.assign(httpArgs, { body: JSON.stringify(postBody) });
      Object.assign(headers, { 'Content-Type': 'application/json' });
    }
  } else {
    Object.assign(httpArgs, { body: postBody });
  }

  Object.assign(httpArgs, {
    headers: new Headers(headers as any),
    method: httpMethod,
    credentials: 'include',
  });

  const updatedPath = path.replace(/^\/v1\.0/, '');

  fetch(`${BACKEND_BASE_URL}${updatedPath}`, httpArgs)
    .then((response) => {
      if (response.status === 401) {
        throw new UnauthenticatedError('You must be authenticated to do this.');
      }
      return response.text().then((result: any) => {
        return { response, text: result };
      });
    })
    .then((result: any) => {
      let jsonResult = null;
      try {
        jsonResult = JSON.parse(result.text);
      } catch (error) {
        const httpStatusMesage = messageForHttpError(
          result.response.status,
          result.response.statusText,
        );
        const baseMessage = `Received unexpected response from server. ${httpStatusMesage}.`;
        console.error(`${baseMessage} Body: ${result.text}`);
        if (error instanceof SyntaxError) {
          throw new UnexpectedResponseError(baseMessage);
        }
        throw error;
      }
      if (result.response.status === 403) {
        if (onUnauthorized) {
          onUnauthorized(jsonResult);
        } else if (UserService.isPublicUser()) {
          window.location.href = '/public/sign-out';
        } else {
          // Hopefully we can make this service a hook and use the error message context directly
          // eslint-disable-next-line no-alert
          alert(jsonResult.message);
        }
      } else if (!result.response.ok) {
        if (failureCallback) {
          failureCallback(jsonResult);
        } else {
          let message = 'A server error occurred.';
          if (jsonResult.message) {
            message = jsonResult.message;
          }
          console.error(message);
          // eslint-disable-next-line no-alert
          alert(message);
        }
      } else {
        successCallback(jsonResult);
      }
    })
    .catch((error) => {
      if (error.name !== 'UnauthenticatedError') {
        if (failureCallback) {
          failureCallback(error);
        } else {
          console.error(error.message);
        }
      } else if (
        !UserService.isLoggedIn() &&
        window.location.pathname !== '/login'
      ) {
        window.location.href = `/login?original_url=${UserService.getCurrentLocation()}`;
      }
    });
};

const HttpService = {
  HttpMethods,
  makeCallToBackend,
  messageForHttpError,
};

export default HttpService;
