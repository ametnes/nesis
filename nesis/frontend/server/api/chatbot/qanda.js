const logger = require('../../util/logger');

//Insight GPT
const post = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;

  const body = request.body;
  if (!body) {
    return response.status(400).send({
      message: 'Invalid request. body not supplied',
    });
  }

  const endpoint = `${url}/modules/qanda/predictions`;
  logger.info(`Getting endpoint ${endpoint}`);
  requests
    .post(endpoint)
    .send(body)
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json')
    .set(
      'Authorization',
      `${
        request.headers && request.headers.authorization
          ? request.headers.authorization
          : ''
      }`,
    )
    .then((res) => {
      response.status(res.status).send(res.body);
    })
    .catch((err) => {
      logger.error(
        `Fail posting to ${url}: ${
          err.response ? JSON.stringify(err.response.body) : ''
        }`,
      );
      response.status(err.status).send(err.response ? err.response.body : '');
    });
};

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;

  const endpoint = `${url}/modules/qanda/predictions`;
  logger.info(`Getting endpoint ${endpoint}`);
  requests
    .get(endpoint)
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
        `Fail getting to ${url}: ${
          err.response ? JSON.stringify(err.response.body) : ''
        }`,
      );
      response.status(err.status).send(err.response ? err.response.body : '');
    });
};

const getById = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const id = request.params.id;
  if (!id) {
    return response.status(400).send({
      message: 'Invalid request. id not supplied',
    });
  }
  const endpoint = `${url}/modules/qanda/predictions/${id}`;
  logger.info(`Getting endpoint ${endpoint}`);
  requests
    .get(endpoint)
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
        `Fail getting to ${url}: ${
          err.response ? JSON.stringify(err.response.body) : ''
        }`,
      );
      response.status(err.status).send(err.response ? err.response.body : '');
    });
};

module.exports = {
  post: post,
  getAll: getAll,
  getById: getById,
};
