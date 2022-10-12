import jwt from 'jwt-decode';
import { BACKEND_BASE_URL } from '../config';

// NOTE: this currently stores the jwt token in local storage
// which is considered insecure. Server set cookies seem to be considered
// the most secure but they require both frontend and backend to be on the same
// domain which we probably can't guarantee. We could also use cookies directly
// but they have the same XSS issues as local storage.
//
// Some explanation:
// https://dev.to/nilanth/how-to-secure-jwt-in-a-single-page-application-cko

const getCurrentLocation = () => {
  // to trim off any query params
  return `${window.location.origin}${window.location.pathname}`;
};

const doLogin = () => {
  const url = `${BACKEND_BASE_URL}/login?redirect_url=${getCurrentLocation()}`;
  window.location.href = url;
};
const getIdToken = () => {
  return localStorage.getItem('jwtIdToken');
};

const doLogout = () => {
  const idToken = getIdToken();
  localStorage.removeItem('jwtAccessToken');
  localStorage.removeItem('jwtIdToken');
  const redirctUrl = `${window.location.origin}/`;
  const url = `${BACKEND_BASE_URL}/logout?redirect_url=${redirctUrl}&id_token=${idToken}`;
  window.location.href = url;
};

const getAuthToken = () => {
  return localStorage.getItem('jwtAccessToken');
};
const isLoggedIn = () => {
  return !!getAuthToken();
};

const getUsername = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwt(idToken);
    return (idObject as any).preferred_username;
  }
  return null;
};

// FIXME: we could probably change this search to a hook
// and then could use useSearchParams here instead
const getAuthTokenFromParams = () => {
  const queryParams = window.location.search;
  const accessTokenMatch = queryParams.match(/.*\baccess_token=([^&]+).*/);
  const idTokenMatch = queryParams.match(/.*\bid_token=([^&]+).*/);
  if (accessTokenMatch) {
    const accessToken = accessTokenMatch[1];
    localStorage.setItem('jwtAccessToken', accessToken);
    if (idTokenMatch) {
      const idToken = idTokenMatch[1];
      localStorage.setItem('jwtIdToken', idToken);
    }
    // to remove token query param
    window.location.href = getCurrentLocation();
  } else if (!isLoggedIn()) {
    doLogin();
  }
};

const hasRole = (_roles: string[]): boolean => {
  return isLoggedIn();
};

const UserService = {
  doLogin,
  doLogout,
  isLoggedIn,
  getAuthToken,
  getAuthTokenFromParams,
  getUsername,
  hasRole,
};

export default UserService;
