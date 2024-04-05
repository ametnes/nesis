import { useMemo } from 'react';
import { API_PREFIX, Client } from './httpClient';
import { useSignOut } from '../SessionContext';

export default function useClient() {
  const signOut = useSignOut();
  return useMemo(() => new Client(API_PREFIX, signOut), [signOut]);
}
