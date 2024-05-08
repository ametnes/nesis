const logger = require('../util/logger');

const post = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const session = request.body;
  const oauth_token_key = profile.NESIS_OAUTH_TOKEN_KEY;

  if (!session || session[oauth_token_key]) {
    return response.status(400).send({
      message: 'Invalid request. session not supplied',
    });
  }

  // session cannot contain the oauth token key
  if (oauth_token_key in session) {
    return response.status(400).send({
      message: 'Invalid request. session not supplied',
    });
  }

  let oauthProvider = null;

  if (session.azure) {
    logger.info(`Loggin with Azure ${session.azure.accessToken}`);
    oauthProvider = authenticateWithAzure(requests, profile, session.azure);
  } else {
    oauthProvider = requests
      .post(`${url}/sessions`)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json')
      .send({ ...session });
  }

  logger.info(`Posting to ${url}/sessions`);

  oauthProvider
    .then((res) => {
      response.status(res.status).send(res.body);
    })
    .catch((err) => {
      logger.error(`Fail posting to ${url}: ${err}, status: ${err.status}`);
      response.status(err.status).send(err.response.body);
    });
};

const _delete = (requests, url) => (request, response) => {
  requests
    .delete(`${url}/sessions`)
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .set(
      'Authorization',
      `${request.headers ? request.headers.authorization : ''}`,
    )
    .then((res) => {
      response.status(res.status).send(res.body);
    })
    .catch((err) => {
      logger.error(
        `Fail posting to ${url}: ${JSON.stringify(
          err.response.body,
        )} with status ${err.status}`,
      );
      response.status(err.status).send(err.response.body);
    });
};

async function authenticateWithAzure(requests, profile, azure) {
  try {
    const url = profile.SERVICE_ENDPOINT;
    const oauth_token_key = profile.NESIS_OAUTH_TOKEN_KEY;
    const oauth_token_value = profile.NESIS_OAUTH_TOKEN_VALUE;

    const email = azure.account.username;
    const name = azure.account.name;

    const payload = {
      email: email,
      name: azure.account.name,
      [oauth_token_key]: oauth_token_value,
    };
    return requests
      .post(`${url}/sessions`)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json')
      .send(payload)
      .then((res) => ({
        status: res.status,
        body: {
          ...res.body,
          email,
          name,
        },
      }));
  } catch (e) {
    console.error(e);
    return Promise.reject(e);
  }
}

module.exports.post = post;
module.exports.delete = _delete;
