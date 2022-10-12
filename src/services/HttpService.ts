import { BACKEND_BASE_URL } from '../config';
import { objectIsEmpty } from '../helpers';
import UserService from './UserService';

const HttpMethods = {
  GET: 'GET',
  POST: 'POST',
  DELETE: 'DELETE',
};

const getBasicHeaders = (): object => {
  if (UserService.isLoggedIn()) {
    return {
      Authorization: `Bearer ${UserService.getAuthToken()}`,
    };
  }
  return {};
};

type backendCallProps = {
  path: string;
  successCallback: Function;
  failureCallback?: Function;
  httpMethod?: string;
  extraHeaders?: object;
  postBody?: any;
};

class UnauthenticatedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UnauthenticatedError';
  }
}

const makeCallToBackend = ({
  path,
  successCallback,
  failureCallback,
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
      Object.assign(httpArgs, { body: JSON.stringify(postBody) });
      Object.assign(headers, { 'Content-Type': 'application/json' });
    }
  } else {
    Object.assign(httpArgs, { body: postBody });
  }

  Object.assign(httpArgs, {
    headers: new Headers(headers as any),
    method: httpMethod,
  });

  let isSuccessful = true;
  fetch(`${BACKEND_BASE_URL}${path}`, httpArgs)
    .then((response) => {
      if (response.status === 401) {
        UserService.doLogin();
        throw new UnauthenticatedError('You must be authenticated to do this.');
      } else if (!response.ok) {
        isSuccessful = false;
      }
      return response.json();
    })
    .then((result: any) => {
      if (isSuccessful) {
        successCallback(result);
      } else {
        let message = 'A server error occurred.';
        if (result.message) {
          message = result.message;
        }
        if (failureCallback) {
          failureCallback(message);
        } else {
          console.error(message);
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'UnauthenticatedError') {
        if (failureCallback) {
          failureCallback(error.message);
        } else {
          console.error(error.message);
        }
      }
    });
};

const HttpService = {
  HttpMethods,
  makeCallToBackend,
};

export default HttpService;
