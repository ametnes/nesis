const STORAGE_KEY = 'AUTH_TOKEN';

export function getToken() {
  return window.sessionStorage.getItem(STORAGE_KEY);
}

export function setToken(token) {
  window.sessionStorage.setItem(STORAGE_KEY, token);
}

export function clearToken() {
  window.sessionStorage.removeItem(STORAGE_KEY);
}
