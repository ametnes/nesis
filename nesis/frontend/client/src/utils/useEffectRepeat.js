import { useEffect } from 'react';
import useStateToggle from './useStateToggle';

export default function useEffectRepeat(callback, dependencyList = []) {
  const [retryPlaceholder, repeat] = useStateToggle();
  useEffect(callback, [retryPlaceholder, ...dependencyList]);
  return repeat;
}
