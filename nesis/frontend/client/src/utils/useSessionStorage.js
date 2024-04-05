import { useState, useEffect, useCallback } from 'react';

export default function useSessionStorage(key) {
  let initialValue;
  if (key && window) {
    initialValue = window.sessionStorage[key];
  }
  const [state, setLocalState] = useState(initialValue);

  const setLocalStorage = useCallback(
    (value) => {
      if (value == null) {
        window.sessionStorage.removeItem(key);
      } else {
        window.sessionStorage.setItem(key, JSON.stringify(value));
      }
      setLocalState(value);
    },
    [setLocalState, key],
  );

  useEffect(() => {
    const value = window.sessionStorage.getItem(key);
    if (value) {
      setLocalState(JSON.parse(value));
    } else {
      setLocalState(null);
    }
  }, [key, setLocalState]);
  return [state, setLocalStorage];
}
