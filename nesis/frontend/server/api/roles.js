const logger = require('../util/logger');

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const endpoint = `${url}/roles`;
  logger.info(`Getting roles endpoint ${endpoint}`);
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
  const roleId = request.params.id;
  if (!roleId) {
    return response.status(400).send({
      message: 'Invalid request. Role name not supplied',
    });
  }
  const endpoint = `${url}/roles/${roleId}`;
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
  const role = request.body;
  if (!role) {
    return response.status(400).send({
      message: 'Invalid request. Role not supplied',
    });
  }

  const endpoint = role.id ? `${url}/roles/${role.id}` : `${url}/roles`;

  logger.info(`Posting endpoint ${endpoint}`);

  const post = role.id === null || role.id === undefined;
  const backEndRequest = (
    post ? requests.post(endpoint) : requests.put(endpoint)
  )
    .send(role)
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
  const roleId = request.params.id;
  if (!roleId || roleId == 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. role Name not supplied',
    });
  }
  const endpoint = `${url}/roles/${roleId}`;
  logger.info(`Getting endpoint ${endpoint}`);
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
  post: post,
  delete: _delete,
};
