const profile = {
  PROD: {
    SERVICE_ENDPOINT: `${process.env.API_URL}/v1`,
    NESIS_OAUTH_TOKEN_KEY: process.env.NESIS_OAUTH_TOKEN_KEY,
    NESIS_OAUTH_TOKEN_VALUE: process.env.NESIS_OAUTH_TOKEN_VALUE,
    NESIS_OAUTH_AZURE_ENABLED: process.env.NESIS_OAUTH_AZURE_ENABLED,
    NESIS_OAUTH_AZURE_CLIENT_ID: process.env.NESIS_OAUTH_AZURE_CLIENT_ID,
    NESIS_OAUTH_AZURE_TENANT_ID: process.env.NESIS_OAUTH_AZURE_TENANT_ID,
    NESIS_OAUTH_AZURE_AUTHORITY: 'https://login.microsoftonline.com/common/',
    NESIS_OAUTH_AZURE_REDIRECTURI: process.env.NESIS_OAUTH_AZURE_REDIRECTURI,
    NESIS_OAUTH_AZURE_CACHELOCATION:
      process.env.NESIS_OAUTH_AZURE_CACHELOCATION || 'sessionStorage',
    NESIS_OAUTH_AZURE_STOREAUTHSTATEINCOOKIE:
      process.env.NESIS_OAUTH_AZURE_STOREAUTHSTATEINCOOKIE || false,
    NESIS_OAUTH_AZURE_SCOPES: process.env.NESIS_OAUTH_AZURE_SCOPES || [
      'User.Read',
    ],
    NESIS_OAUTH_GOOGLE_ENABLED: process.env.NESIS_OAUTH_GOOGLE_ENABLED,
    NESIS_OAUTH_GOOGLE_CLIENT_ID: process.env.NESIS_OAUTH_GOOGLE_CLIENT_ID,
    NESIS_OAUTH_GOOGLE_CLIENT_SECRET:
      process.env.NESIS_OAUTH_GOOGLE_CLIENT_SECRET,
    NESIS_OAUTH_GOOGLE_REDIRECTURI: process.env.NESIS_OAUTH_GOOGLE_REDIRECTURI,
  },
  DEV: {
    SERVICE_ENDPOINT: `http://localhost:6000/v1`,
    NESIS_OAUTH_TOKEN_KEY: '___nesis_oauth_token_key___',
    NESIS_OAUTH_TOKEN_VALUE: '___nesis_oauth_token_value___',
    NESIS_OAUTH_AZURE_ENABLED: false,
    NESIS_OAUTH_AZURE_CLIENT_ID: process.env.NESIS_OAUTH_AZURE_CLIENT_ID,
    NESIS_OAUTH_AZURE_TENANT_ID: process.env.NESIS_OAUTH_AZURE_TENANT_ID,
    NESIS_OAUTH_AZURE_AUTHORITY: 'https://login.microsoftonline.com/common/',
    NESIS_OAUTH_AZURE_REDIRECTURI: 'http://localhost:3000/',
    NESIS_OAUTH_AZURE_CACHELOCATION:
      process.env.NESIS_OAUTH_AZURE_CACHELOCATION || 'localStorage',
    NESIS_OAUTH_AZURE_STOREAUTHSTATEINCOOKIE:
      process.env.NESIS_OAUTH_AZURE_STOREAUTHSTATEINCOOKIE || false,
    NESIS_OAUTH_AZURE_SCOPES: process.env.NESIS_OAUTH_AZURE_SCOPES || [
      'User.Read',
    ],
    NESIS_OAUTH_GOOGLE_ENABLED: false,
    NESIS_OAUTH_GOOGLE_CLIENT_ID: process.env.NESIS_OAUTH_GOOGLE_CLIENT_ID,
    NESIS_OAUTH_GOOGLE_CLIENT_SECRET:
      process.env.NESIS_OAUTH_GOOGLE_CLIENT_SECRET,
    NESIS_OAUTH_GOOGLE_REDIRECTURI: 'http://localhost:3000/',
  },
};

module.exports.profile = profile;
