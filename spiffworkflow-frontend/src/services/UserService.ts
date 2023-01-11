import jwt from 'jwt-decode';
import cookie from 'cookie';
import { BACKEND_BASE_URL } from '../config';

// NOTE: this currently stores the jwt token in local storage
// which is considered insecure. Server set cookies seem to be considered
// the most secure but they require both frontend and backend to be on the same
// domain which we probably can't guarantee. We could also use cookies directly
// but they have the same XSS issues as local storage.
//
// Some explanation:
// https://dev.to/nilanth/how-to-secure-jwt-in-a-single-page-application-cko

const getCookie = (key: string) => {
  const parsedCookies = cookie.parse(document.cookie);
  if (key in parsedCookies) {
    return parsedCookies[key];
  }
  return null;
};

// const getCurrentLocation = (queryParams: string = window.location.search) => {
const getCurrentLocation = () => {
  const queryParamString = '';
  // if (queryParams) {
  //   queryParamString = `?${queryParams}`;
  // }
  return `${window.location.origin}${window.location.pathname}${queryParamString}`;
};

const doLogin = () => {
  const url = `${BACKEND_BASE_URL}/login?redirect_url=${getCurrentLocation()}`;
  console.log('URL', url);
  window.location.href = url;
};

// Use access_token for now since it seems to work but if we need the
// id token then set that in a cookie in backend as well
const getIdToken = () => {
  return getCookie('access_token');
};

const doLogout = () => {
  const idToken = getIdToken();
  const redirectUrl = `${window.location.origin}`;
  const url = `${BACKEND_BASE_URL}/logout?redirect_url=${redirectUrl}&id_token=${idToken}`;
  window.location.href = url;
};

const getAccessToken = () => {
  return getCookie('access_token');
};
const isLoggedIn = () => {
  return !!getAccessToken();
};

const getUserEmail = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwt(idToken);
    return (idObject as any).email;
  }
  return null;
};

const getPreferredUsername = () => {
  const idToken = getIdToken();
  if (idToken) {
    const idObject = jwt(idToken);
    return (idObject as any).preferred_username;
  }
  return null;
};

const loginIfNeeded = () => {
  if (!isLoggedIn()) {
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
  getAccessToken,
  loginIfNeeded,
  getPreferredUsername,
  getUserEmail,
  hasRole,
};

export default UserService;
