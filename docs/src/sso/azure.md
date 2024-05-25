# Setup SSO with Azure

## Register your application with Azure
First register your application with Azure using the steps described <a href="https://learn.microsoft.com/en-us/azure/active-directory-b2c/client-credentials-grant-flow?pivots=b2c-user-flow" _blank>here</a>

Take note of these;

2. Azure Client ID
2. Azure Tenant ID

## Configure Nesis
To configure Nesis for Azure, set these environment variables for the respective microservices

### Frontend

In the frontend, set

```
NESIS_OAUTH_AZURE_ENABLED: true
NESIS_OAUTH_AZURE_CLIENT_ID: 00000000-0000-0000-0000-000000000
NESIS_OAUTH_AZURE_REDIRECTURI: http[s]://your.nesis.host.name/
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

You should now be able to authenticate with Microsoft Azure
