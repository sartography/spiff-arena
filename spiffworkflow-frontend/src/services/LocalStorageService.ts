/**
 * Straightforward encapsulation of typical LocalStorage functions.
 * TODO: This should probably be async, have error handling, etc.,
 * but for now all we need is the basic accessors.
 */

const LAST_PROCESS_INSTANCE_RUN_LOCATION = "lastProcessInstanceRunLocation";
const SPIFF_FAVORITES = 'spifffavorites';

const getStorageValue = (key: string) => {
  // Some concession to error handling here.
  return localStorage.getItem(key) || '[]';
};

const setStorageValue = (key: string, value: string) => {
  localStorage.setItem(key, value);
};

const removeStorageValue = (key: string) => {
  localStorage.removeItem(key);
};

const getAndRemoveLastProcessInstanceRunLocation = () => {
  const location = localStorage.getItem(LAST_PROCESS_INSTANCE_RUN_LOCATION);
  localStorage.removeItem(LAST_PROCESS_INSTANCE_RUN_LOCATION);
  return location;
};

const setLastProcessInstanceRunLocation = (value: string) => {
  localStorage.setItem(LAST_PROCESS_INSTANCE_RUN_LOCATION, value);
};

export {
  SPIFF_FAVORITES,
  getStorageValue,
  setStorageValue,
  removeStorageValue,
  getAndRemoveLastProcessInstanceRunLocation,
  setLastProcessInstanceRunLocation,
};
