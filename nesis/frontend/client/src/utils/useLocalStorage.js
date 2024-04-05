import { useState, useEffect, useCallback } from 'react';

export default function useLocalStorage(key) {
  let initialValue;
  if (key && window) {
    initialValue = window.localStorage[key];
  }
  const [state, setLocalState] = useState(initialValue);

  const setLocalStorage = useCallback(
    (value) => {
      if (value == null) {
        window.localStorage.removeItem(key);
      } else {
        window.localStorage.setItem(key, JSON.stringify(value));
      }
      setLocalState(value);
    },
    [setLocalState, key],
  );

  useEffect(() => {
    const value = window.localStorage.getItem(key);
    if (value) {
      setLocalState(JSON.parse(value));
    } else {
      setLocalState(null);
    }
  }, [key, setLocalState]);
  return [state, setLocalStorage];
}
