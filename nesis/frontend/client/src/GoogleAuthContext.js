import React from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { useConfig } from './ConfigContext';

const DefaultConfigContext = React.createContext({});

export default function GoogleContextProvider({ children }) {
  const config = useConfig();
  const google_client_id = config?.auth?.OAUTH_GOOGLE_CLIENT_ID;
  const googleAuthEnabled =
    google_client_id && config?.auth?.OAUTH_GOOGLE_ENABLED;
  return (
    <>
      {googleAuthEnabled ? (
        <GoogleOAuthProvider
          value={google_client_id}
          clientId={google_client_id}
        >
          {children}
        </GoogleOAuthProvider>
      ) : (
        <DefaultConfigContext.Provider value={googleAuthEnabled}>
          {children}
        </DefaultConfigContext.Provider>
      )}
    </>
  );
}
