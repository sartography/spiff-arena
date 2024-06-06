const SPIFF_FAVORITES = 'spifffavorites';

const getStorageValue = (key: string) => {
  return localStorage.getItem(key) || '[]';
};

const setStorageValue = (key: string, value: string) => {
  localStorage.setItem(key, value);
};

const removeStorageValue = (key: string) => {
  localStorage.removeItem(key);
};

export {
  SPIFF_FAVORITES,
  getStorageValue,
  setStorageValue,
  removeStorageValue,
};
