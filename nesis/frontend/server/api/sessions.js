const logger = require('../util/logger');
const querystring = require('querystring');
const { OAuth2Client } = require('google-auth-library');

const post = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const session = request.body;
  const oauth_token_key = profile.NESIS_OAUTH_TOKEN_KEY;

  // session cannot contain the oauth token key
  if (!session || oauth_token_key in session) {
    return response.status(400).send({
      message: 'Invalid request. session not supplied',
    });
  }

  let oauthProvider = null;

  if (session.azure) {
    oauthProvider = authenticateWithAzure(requests, profile, session.azure);
  } else if (session.google) {
    oauthProvider = authenticateWithGoogle(requests, profile, session.google);
  } else {
    oauthProvider = requests
      .post(`${url}/sessions`)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json')
      .send({ ...session });
  }

  oauthProvider
    .then((res) => {
      response.status(res.status).send(res.body);
    })
    .catch((err) => {
      if (err && err.response && err.response.body) {
        response.status(err.status).send(err.response.body);
      } else if (err) {
        response.status(err.status || 400).send('Error processing request');
      } else {
        response.status(500).send('Error processing request');
      }
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
        `Fail posting to ${url}: ${JSON.stringify(err)} with status ${err.status
        }`,
      );
      response.status(err.status).send(err.response.body);
    });
};

function authenticateWithAzure(requests, profile, azure) {
  const email = azure.account.username;
  const name = azure.account.name;

  const graphUrl = 'https://graph.microsoft.com/v1.0/me';

  return requests
    .get(graphUrl)
    .set('Authorization', `Bearer ${azure.accessToken}`)
    .set('Content-Type', 'application/json')
    .send()
    .then((res) => {
      if (res.body.mail !== email) {
        const messsage = 'Invalid azure access token';
        const error = new Error(messsage);
        Object.assign(error, {
          status: 401,
          response: {
            body: 'Invalid azure access token',
          },
        });
        throw error;
      }
    })
    .then(() => sendOauthSession(requests, name, email, profile));
}

function authenticateWithGoogle(requests, profile, code) {
  const grant_type = 'authorization_code';
  const googleApiUrl = 'https://oauth2.googleapis.com/token';

  const payload = {
    client_id: profile.NESIS_OAUTH_GOOGLE_CLIENT_ID,
    client_secret: profile.NESIS_OAUTH_GOOGLE_CLIENT_SECRET,
    redirect_uri: profile.NESIS_OAUTH_GOOGLE_REDIRECTURI,
    grant_type: grant_type,
    code: code
  }

  const body = querystring.stringify(payload);
  return requests
    .post(googleApiUrl)
    .set('Content-Type', 'application/x-www-form-urlencoded')
    .send(body)
    .then((response) => {
      const resp = response.body
      return verifyToken(payload.client_id, resp.id_token);

    }).then((userInfo) =>
      sendOauthSession(requests, userInfo.name, userInfo.email, profile),
    )
    .catch((e) => {
      const messsage = 'Invalid azure access token';
      const error = new Error(messsage);
      Object.assign(error, {
        status: 401,
        response: {
          body: 'Invalid azure access token',
        },
      });
      throw error;
    });
}

async function verifyToken(client_id, jwtToken) {
  const client = new OAuth2Client(client_id);
  // Call the verifyIdToken to verify and decode it
  const ticket = await client.verifyIdToken({
    idToken: jwtToken,
    audience: client_id,
  });
  // Get the JSON with all the user info
  const payload = ticket.getPayload();
  // This is a JSON object that contains all the user info
  return payload;
}

function sendOauthSession(requests, name, email, profile) {
  const url = profile.SERVICE_ENDPOINT;
  const oauth_token_key = profile.NESIS_OAUTH_TOKEN_KEY;
  const oauth_token_value = profile.NESIS_OAUTH_TOKEN_VALUE;
  const payload = {
    email: email,
    name: name,
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
}

module.exports.post = post;
module.exports.delete = _delete;
