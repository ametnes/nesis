import { useState, useRef, useMemo } from 'react';
import useClient from './useClient';
import useEffectRepeat from './useEffectRepeat';
import parseApiErrorMessage from './parseApiErrorMessage';

export default function useApiGet(path) {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const client = useClient();
  const unmounted = useRef(false);

  const repeat = useEffectRepeat(() => {
    unmounted.current = false;
    setIsLoading(true);
    client
      .get(path)
      .then((res) => {
        if (!unmounted.current) {
          setResult(res.body);
        }
      })
      .catch((e) => setError(parseApiErrorMessage(e)))
      .finally(() => {
        if (!unmounted.current) {
          setIsLoading(false);
        }
      });
    return () => {
      unmounted.current = true;
    };
  }, [path, client, setResult, setError, unmounted]);

  const actions = useMemo(() => ({ repeat }), [repeat]);

  return [result, isLoading, error, actions];
}
