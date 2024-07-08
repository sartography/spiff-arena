import { jwtDecode } from 'jwt-decode';
import cookie from 'cookie';
import { BACKEND_BASE_URL } from '../config';
import { AuthenticationOption } from '../interfaces';
import { parseTaskShowUrl } from '../helpers';

// NOTE: this currently stores the jwt token in local storage
// which is considered insecure. Server set cookies seem to be considered
// the most secure but they require both frontend and backend to be on the same
// domain which we probably can't guarantee. We could also use cookies directly
// but they have the same XSS issues as local storage.
//
// Some explanation:
// https://dev.to/nilanth/how-to-secure-jwt-in-a-single-page-application-cko

const SIGN_IN_PATH = '/';

const getCookie = (key: string) => {
  const parsedCookies = cookie.parse(document.cookie);
  if (key in parsedCookies) {
    return parsedCookies[key];
  }
  return null;
};

const getCurrentLocation = (queryParams: string = window.location.search) => {
  let queryParamString = '';
  if (queryParams) {
    queryParamString = `${queryParams}`;
  }
  return encodeURIComponent(
    `${window.location.origin}${window.location.pathname}${queryParamString}`,
  );
};

const checkPathForTaskShowParams = (
  redirectUrl: string = window.location.pathname,
) => {
  const pathSegments = parseTaskShowUrl(redirectUrl);
  if (pathSegments) {
    return { process_instance_id: pathSegments[1], task_guid: pathSegments[2] };
  }
  return null;
};

// required for logging out
const getIdToken = () => {
  return getCookie('id_token');
};
const getAccessToken = () => {
  return getCookie('access_token');
};
const getAuthenticationIdentifier = () => {
  return getCookie('authentication_identifier');
};

const isLoggedIn = () => {
  return !!getAccessToken();
};

const isPublicUser = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwtDecode(idToken);
    return (idObject as any).public;
  }
  return false;
};

const doLogin = (
  authenticationOption?: AuthenticationOption,
  redirectUrl?: string | null,
) => {
  const taskShowParams = checkPathForTaskShowParams(redirectUrl || undefined);
  const loginParams = [`redirect_url=${redirectUrl || getCurrentLocation()}`];
  if (taskShowParams) {
    loginParams.push(
      `process_instance_id=${taskShowParams.process_instance_id}`,
    );
    loginParams.push(`task_guid=${taskShowParams.task_guid}`);
  }
  if (authenticationOption) {
    loginParams.push(
      `authentication_identifier=${authenticationOption.identifier}`,
    );
  }
  const url = `${BACKEND_BASE_URL}/login?${loginParams.join('&')}`;
  window.location.href = url;
};

const doLogout = () => {
  const idToken = getIdToken();

  const frontendBaseUrl = window.location.origin;
  let logoutRedirectUrl = `${BACKEND_BASE_URL}/logout?redirect_url=${frontendBaseUrl}&id_token=${idToken}&authentication_identifier=${getAuthenticationIdentifier()}`;

  // edge case. if the user is already logged out, just take them somewhere that will force them to sign in.
  if (idToken === null) {
    logoutRedirectUrl = SIGN_IN_PATH;
  } else if (isPublicUser()) {
    logoutRedirectUrl += '&backend_only=true';
  }

  window.location.href = logoutRedirectUrl;
};

const getUserEmail = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwtDecode(idToken);
    return (idObject as any).email;
  }
  return null;
};

const authenticationDisabled = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwtDecode(idToken);
    return (idObject as any).authentication_disabled;
  }
  return false;
};

/**
 * Return prefered username
 * Somehow if using Google as the OpenID provider, the field `preferred_username` is not returned
 * therefore a special handling is added to cover the issue.
 * Please refer to following link, section 5.1 Standard Claims to find the details:
 * https://openid.net/specs/openid-connect-core-1_0.html
 * @returns string
 */
const getPreferredUsername = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwtDecode(idToken);

    if (idToken === undefined || idToken === 'undefined') {
      return null;
    }

    if ((idObject as any).preferred_username !== undefined) {
      return (idObject as any).preferred_username;
    }

    if ((idObject as any).name !== undefined) {
      // note: handling response if OpenID is using Google SSO as the provider
      return (idObject as any).name;
    }

    // fallback to `given_name` as the default value.
    return (idObject as any).given_name;
  }

  return null;
};

const loginIfNeeded = () => {
  if (!isLoggedIn()) {
    doLogin();
  }
};

const UserService = {
  authenticationDisabled,
  doLogin,
  doLogout,
  getAccessToken,
  getAuthenticationIdentifier,
  getCurrentLocation,
  getPreferredUsername,
  getUserEmail,
  isLoggedIn,
  isPublicUser,
  loginIfNeeded,
};

export default UserService;
