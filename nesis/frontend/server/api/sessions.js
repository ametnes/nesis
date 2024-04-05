const logger = require('../util/logger');

const post = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const session = request.body;

  if (!session) {
    return response.status(400).send({
      message: 'Invalid request. session not supplied',
    });
  }

  logger.info(`Posting to ${url}/sessions`);
  requests
    .post(`${url}/sessions`)
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .send(session)
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

module.exports.post = post;
module.exports.delete = _delete;
