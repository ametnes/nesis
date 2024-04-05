const logger = require('../util/logger');

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const module = request.params.module;
  const endpoint = `${url}/modules/${module}/settings`;
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
  const settingsId = request.params.id;
  const module = request.params.module;
  if (!settingsId) {
    return response.status(400).send({
      message: 'Invalid request. Setting id not supplied',
    });
  }
  const endpoint = `${url}/modules/${module}/settings/${settingsId}`;
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
  const datasource = request.body;
  const module = request.params.module;
  if (!datasource) {
    return response.status(400).send({
      message: 'Invalid request. Datasource not supplied',
    });
  }

  const endpoint = `${url}/modules/${module}/settings`;
  logger.info(`Getting endpoint ${endpoint}`);
  requests
    .post(endpoint)
    .send(datasource)
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

const _delete = (requests, profile) => (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const id = request.params.id;
  const module = request.params.module;
  if (!id || id == 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. datasource Name not supplied',
    });
  }
  const endpoint = `${url}/modules/${module}/settings/${id}`;
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
