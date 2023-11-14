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

  let isSuccessful = true;
  // this fancy 403 handling is like this because we want to get the response body.
  // otherwise, we would just throw an exception.
  let is403 = false;
  fetch(`${BACKEND_BASE_URL}${updatedPath}`, httpArgs)
    .then((response) => {
      if (response.status === 401) {
        throw new UnauthenticatedError('You must be authenticated to do this.');
      } else if (response.status === 403) {
        is403 = true;
        isSuccessful = false;
      } else if (!response.ok) {
        isSuccessful = false;
      }
      return response.json();
    })
    .then((result: any) => {
      if (isSuccessful) {
        successCallback(result);
      } else if (is403) {
        if (onUnauthorized) {
          onUnauthorized(result);
        } else {
          // Hopefully we can make this service a hook and use the error message context directly
          // eslint-disable-next-line no-alert
          alert(result.message);
        }
      } else {
        let message = 'A server error occurred.';
        if (result.message) {
          message = result.message;
        }
        if (failureCallback) {
          failureCallback(result);
        } else {
          console.error(message);
          // eslint-disable-next-line no-alert
          alert(message);
        }
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
};

export default HttpService;
