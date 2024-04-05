import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import PropTypes from 'prop-types';
import { clearToken } from './utils/tokenStorage';
import { useHistory } from 'react-router-dom';
import useSessionStorage from './utils/useSessionStorage';
import apiClient from './utils/httpClient';
const SessionContext = React.createContext({
  session: null,
  setSession: () => '',
});

SessionProvider.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]).isRequired,
};

export default SessionContext;

const SESSION_KEY = 'AMETNES_CURRENT_SESSION';

export function SessionProvider({ children }) {
  const [session, setSession] = useSessionStorage(SESSION_KEY);
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (!session) {
      return;
    }
  }, [session, apiClient, setSession, setUser]);

  const value = useMemo(
    () => ({ session, setSession, user }),
    [session, setSession, user],
  );
  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useCurrentSession() {
  const context = useContext(SessionContext);
  return context && context.session;
}

export function useCurrentUser() {
  const context = useContext(SessionContext);
  return context && context.user;
}

export function useSignOut(client) {
  const context = useContext(SessionContext);
  const setSession = context?.setSession;
  const history = useHistory();
  return useCallback(
    function () {
      logoutFromGoogle();
      logoutFromOptimAI(client);
      clearToken();
      setSession(null);
      history.push('/signin');
    },
    [setSession, history],
  );
}

function logoutFromGoogle() {
  if (window.gapi && window.gapi.auth2) {
    const auth2 = window.gapi.auth2.getAuthInstance();
    if (auth2 != null) {
      auth2.signOut().then(auth2.disconnect());
    }
  }
}

function logoutFromOptimAI(client) {
  if (!client) {
    return;
  }
  client
    .delete('sessions')
    .then((res) => {
      /** Ignored */
    })
    .catch((err) => {
      /** Ignored */
    });
}
