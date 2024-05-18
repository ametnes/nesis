const getConfig = (requests, profile) => (request, response) => {
  const config = {
    version: 'v1',
    auth: {
      OAUTH_AZURE_ENABLED: profile.NESIS_OAUTH_AZURE_ENABLED,
      OAUTH_AZURE_CLIENT_ID: profile.NESIS_OAUTH_AZURE_CLIENT_ID,
      OAUTH_AZURE_AUTHORITY: profile.NESIS_OAUTH_AZURE_AUTHORITY,
      OAUTH_AZURE_REDIRECTURI: profile.NESIS_OAUTH_AZURE_REDIRECTURI,
      OAUTH_AZURE_CACHELOCATION: profile.NESIS_OAUTH_AZURE_CACHELOCATION,
      OAUTH_AZURE_STOREAUTHSTATEINCOOKIE:
        profile.NESIS_OAUTH_AZURE_STOREAUTHSTATEINCOOKIE,
      OAUTH_AZURE_SCOPES: profile.NESIS_OAUTH_AZURE_SCOPES || ['User.Read'],
      OAUTH_GOOGLE_ENABLED: profile.NESIS_OAUTH_GOOGLE_ENABLED,
      OAUTH_GOOGLE_CLIENT_ID: profile.NESIS_OAUTH_GOOGLE_CLIENT_ID,
    },
  };
  response.status(200).send(JSON.stringify(config));
};

module.exports = {
  get: getConfig,
};
