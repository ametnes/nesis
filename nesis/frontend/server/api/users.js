const { json } = require('body-parser');
const logger = require('../util/logger');

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const endpoint = `${url}/users`;
  logger.info(`Getting users endpoint ${endpoint}`);
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
  const userId = request.params.id;
  if (!userId) {
    return response.status(400).send({
      message: 'Invalid request. Role name not supplied',
    });
  }
  const endpoint = `${url}/users/${userId}`;
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

const getRoles = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const userId = request.params.id;
  if (!userId || userId == undefined || userId === 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. Role name not supplied',
    });
  }
  const endpoint = `${url}/users/${userId}/roles`;
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

const post = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const user = request.body;
  if (!user) {
    return response.status(400).send({
      message: 'Invalid request. Role not supplied',
    });
  }

  const endpoint = user.id ? `${url}/users/${user.id}` : `${url}/users`;

  logger.info(`Posting endpoint ${endpoint}`);

  const post = user.id === null || user.id === undefined;
  const backEndRequest = (
    post ? requests.post(endpoint) : requests.put(endpoint)
  )
    .send(user)
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json');

  // logger.info(`User backend request header ${JSON.stringify(request.headers)}`);

  if (request.headers && request.headers.authorization) {
    backEndRequest.set('Authorization', request.headers.authorization);
  }

  backEndRequest
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

const _delete = (requests, profile) => (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const userId = request.params.id;
  if (!userId || userId == 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. user Name not supplied',
    });
  }
  const endpoint = `${url}/users/${userId}`;
  logger.info(`Deleting endpoint ${endpoint}`);
  requests
    .delete(endpoint)
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
        `Fail deleting to ${url}: ${
          err.response ? JSON.stringify(err.response.body) : ''
        }`,
      );
      response.status(err.status).send(err.response ? err.response.body : '');
    });
};

module.exports = {
  getAll: getAll,
  getById: getById,
  getRoles: getRoles,
  post: post,
  delete: _delete,
};
