import React from 'react';
import useClient from '../utils/useClient';
import { useConfig } from '../ConfigContext';
import parseApiErrorMessage from '../utils/parseApiErrorMessage';
import { PublicClientApplication } from '@azure/msal-browser';
import AzureIcon from '../images/AzureIcon.png';
import classes from '../styles/SignInPage.module.css';

export default function AzureButton({ onFailure, onSuccess }) {
  const config = useConfig();
  const client = useClient();

  const handleLogin = async (evt) => {
    evt.preventDefault();
    const msalInstance = new PublicClientApplication({
      auth: {
        clientId: config?.auth?.OAUTH_AZURE_CLIENT_ID,
        authority: config?.auth?.OAUTH_AZURE_AUTHORITY,
        redirectUri: config?.auth?.OAUTH_AZURE_REDIRECTURI,
      },
      cache: {
        cacheLocation: config?.auth?.OAUTH_AZURE_CACHELOCATION,
        storeAuthStateInCookie:
          config?.auth?.OAUTH_AZURE_STOREAUTHSTATEINCOOKIE,
      },
    });
    await msalInstance.initialize();
    await msalInstance
      .loginPopup({
        scopes: config?.AZURE_SCOPES || ['User.Read'],
      })
      .then(async (response) => {
        console.log(response);
        if (response?.accessToken) {
          client
            .post('sessions', {
              azure: response,
            })
            .then((response) => {
              onSuccess(response?.body?.email, response);
            })
            .catch((error) => {
              onFailure(parseApiErrorMessage(error));
            });
        } else if (onFailure) {
          onFailure('Could not login using Azure');
        }
      })
      .catch((error) => {
        onFailure(parseApiErrorMessage(error));
      });
  };

  return (
    <>
      <button className={`${classes.orloginbutton} my-3`} onClick={handleLogin}>
        <img className={`${classes.loginorimg} mx-1`} src={AzureIcon} />
        Continue With Microsoft
      </button>
    </>
  );
}
