# Setup SSO with Google

## Register your application with Google
First register your application with Google using the steps described <a href="https://support.google.com/cloud/answer/6158849?hl=en#zippy=%2Cweb-applications%2Cstep-create-a-new-client-secret" target="_blank">here</a>.

Take note of these;

2. Google Client ID
2. Google Client Secret

## Configure Nesis
To configure Nesis for Google, set these environment variables for the respective microservices;

### Frontend

In the frontend, set

```
NESIS_OAUTH_GOOGLE_ENABLED: true
NESIS_OAUTH_GOOGLE_CLIENT_ID: 00000000-0000-0000-0000-000000000
NESIS_OAUTH_GOOGLE_CLIENT_SECRET: your.google.client.secret
NESIS_OAUTH_GOOGLE_REDIRECTURI: http[s]://your.nesis.host.name/
NESIS_OAUTH_TOKEN_KEY: __some__random_secure_key___
NESIS_OAUTH_TOKEN_VALUE: ___some___other___very__random___key
```

In the api service, set
```
NESIS_OAUTH_TOKEN_KEY: __some__random_secure_key___
NESIS_OAUTH_TOKEN_VALUE: ___some___other___very__random___key
```

!!! warning "Important"

    The key `NESIS_OAUTH_TOKEN_KEY` and value `NESIS_OAUTH_TOKEN_VALUE` must match in both services.

You should now be able to authenticate with Google.
