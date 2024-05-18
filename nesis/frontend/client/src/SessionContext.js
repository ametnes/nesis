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
import { PublicClientApplication } from '@azure/msal-browser';
import { googleLogout } from '@react-oauth/google';

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

const SESSION_KEY = 'NESIS_CURRENT_SESSION';

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

export function useSignOut(client, config) {
  const context = useContext(SessionContext);
  const setSession = context?.setSession;
  const history = useHistory();
  return useCallback(
    function () {
      logoutNesis(client);
      clearToken();
      setSession(null);
      logoutMicrosoft(config);
      logoutGoogle();
      history.push('/signin');
    },
    [setSession, history],
  );
}

async function logoutMicrosoft(config) {
  try {
    const msalInstance = new PublicClientApplication({
      auth: {
        clientId: config?.auth?.OAUTH_AZURE_CLIENT_ID,
        authority: config?.auth?.OAUTH_AZURE_AUTHORITY,
        redirectUri: config?.auth?.OAUTH_AZURE_REDIRECTURI,
        postLogoutRedirectUri: 'http://localhost:3000/',
      },
    });
    await msalInstance.initialize();
    msalInstance.logoutRedirect();
  } catch (e) {
    /* ignored */
  }
}

async function logoutGoogle() {
  googleLogout();
}

function logoutNesis(client) {
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
