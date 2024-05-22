import React, { useEffect } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import useClient from '../utils/useClient';
import parseApiErrorMessage from '../utils/parseApiErrorMessage';
import GoogleIcon from '../images/GoogleIcon.png';
import classes from '../styles/SignInPage.module.css';
import { useConfig } from '../ConfigContext';

export default function GoogleButton({ onFailure, onSuccess }) {
  const client = useClient();
  const config = useConfig();

  const googleLogin = useGoogleLogin({
    ux_mode: 'redirect',
    flow: 'auth-code',
    redirect_uri: config?.auth?.OAUTH_GOOGLE_REDIRECTURI,
  });

  useEffect(() => {
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const codeParam = urlParams.get('code');

    if (codeParam) {
      client
        .post('sessions', {
          google: codeParam,
        })
        .then((response) => {
          onSuccess(response?.body?.email, response);
        })
        .catch((error) => {
          onFailure(parseApiErrorMessage(error));
        });
    } else {
      const error = 'Failed to Login';
      handleFailure(error);
    }
  }, []);

  function handleFailure(error) {
    onFailure('Could not login using Google');
  }

  return (
    <>
      <button className={`${classes.orloginbutton} my-3`} onClick={googleLogin}>
        <img
          alt="Sign in with Google"
          className={`${classes.loginorimg} mx-1`}
          src={GoogleIcon}
        />
        Sign in with Google
      </button>
    </>
  );
}
