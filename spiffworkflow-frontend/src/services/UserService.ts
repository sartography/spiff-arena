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
const getIdToken = () => {
  return localStorage.getItem('jwtIdToken');
};

const doLogout = () => {
  const idToken = getIdToken();
  localStorage.removeItem('jwtAccessToken');
  localStorage.removeItem('jwtIdToken');
  const redirectUrl = `${window.location.origin}`;
  const url = `${BACKEND_BASE_URL}/logout?redirect_url=${redirectUrl}&id_token=${idToken}`;
  window.location.href = url;
};

const getAuthToken = () => {
  return localStorage.getItem('jwtAccessToken');
};
const isLoggedIn = () => {
  return !!getAuthToken();
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

// FIXME: we could probably change this search to a hook
// and then could use useSearchParams here instead
const getAuthTokenFromParams = () => {
  const queryParams = new URLSearchParams(window.location.search);
  const accessToken = queryParams.get('access_token');
  const idToken = queryParams.get('id_token');

  queryParams.delete('access_token');
  queryParams.delete('id_token');

  if (accessToken) {
    localStorage.setItem('jwtAccessToken', accessToken);
    if (idToken) {
      localStorage.setItem('jwtIdToken', idToken);
    }
    // window.location.href = `${getCurrentLocation(queryParams.toString())}`;
    console.log('THE PALCE: ', `${getCurrentLocation()}`);
    window.location.href = `${getCurrentLocation()}`;
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
  getPreferredUsername,
  getUserEmail,
  hasRole,
};

export default UserService;
