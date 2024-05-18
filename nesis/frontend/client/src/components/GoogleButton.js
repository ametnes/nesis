import React from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import useClient from '../utils/useClient';
import parseApiErrorMessage from '../utils/parseApiErrorMessage';
import GoogleIcon from '../images/GoogleIcon.png';
import classes from '../styles/SignInPage.module.css';

export default function GoogleButton({ onFailure, onSuccess}) {
  const client = useClient();  

 const googleLogin = useGoogleLogin( {
    onSuccess: (tokenRespose) => {
        client.post('sessions', { google: tokenRespose})
        .then((response) => {
            onSuccess(response?.body?.email, response);
        })
        .catch((error) => {
            onFailure(parseApiErrorMessage(error));
        })
    },
    onError: (error) => {
        handleFailure(error);
    }

 });

  function handleFailure(error) {
    onFailure('Could not login using Google');
  }

  return (
    <>
     <button className={`${classes.orloginbutton} my-3`} onClick={googleLogin}>
        <img className={`${classes.loginorimg} mx-1`} src={GoogleIcon} />
        Sign in with Google
      </button>
    </>
  );
}
