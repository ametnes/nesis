import React from 'react';
import { GoogleLogin, useGoogleLogin } from '@react-oauth/google';
import useClient from '../utils/useClient';
import { useConfig } from '../ConfigContext';
import parseApiErrorMessage from '../utils/parseApiErrorMessage';
import {jwtDecode } from 'jwt-decode';
import { ReactComponent as GoogleIcon } from '../images/GoogleIcon.svg';
import classes from '../styles/SignInPage.module.css';

export default function GoogleButton({ onFailure, onSuccess}) {
  const client = useClient();
  const config = useConfig();
  

  function login(response) {
    console.log(response)
    if (response.credential) {
        const resp_token = jwtDecode(response.credential);
        console.log('token: ' + resp_token)
      client
        .post('sessions', { google: resp_token })
        .then((response) => {
            console.log('session resp: ' + response);
          onSuccess(response?.body?.email, response);
        })
        .catch((error) => {
            console.log('session error: ' +  error)
          onFailure(parseApiErrorMessage(error));
        });
    } else if (onFailure) {
      onFailure('Could not login using Google');
    }
  }

 const googleLogin = useGoogleLogin( {
    onSuccess: (tokenRespose) => {
        console.log(tokenRespose);
        client.post('sessions', { google: tokenRespose})
        .then((response) => {
            onSuccess(response?.body?.email, response);
        })
        .catch((error) => {
            console.log('ERROR: ' + error);
            console.log(error);
            onFailure(parseApiErrorMessage(error));
        })
    },
    onError: (error) => {
        handleFailure(error);
    }

 });

  function handleFailure(error) {
    console.error(error);
    onFailure('Could not login using Google');
  }


  return (
    // <div>
    //   <GoogleLogin
    //     clientId={config?.GOOGLE_CLIENT_ID}
    //     text="Continue With Google"
    //     onSuccess={login}
    //     onError={handleFailure}
    //     //cookiePolicy={'single_host_origin'}
    //     responseType="code,token"
    //     size='large'
    //     //width='400'
    //   />
    // </div>
    <>
     <button className={`${classes.orloginbutton} my-3`} onClick={googleLogin}>
        <img className={`${classes.loginorimg} mx-1`} src={GoogleIcon} />
        Sign in with Google
      </button>
    </>
  );
}
