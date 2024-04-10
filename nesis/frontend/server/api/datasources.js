const logger = require('../util/logger');

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const endpoint = `${url}/datasources`;
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
  const datasourceId = request.params.id;
  if (!datasourceId) {
    return response.status(400).send({
      message: 'Invalid request. Datasource name not supplied',
    });
  }
  const endpoint = `${url}/datasources/${datasourceId}`;
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
  if (!datasource) {
    return response.status(400).send({
      message: 'Invalid request. Datasource not supplied',
    });
  }

  const post = datasource.id === null || datasource.id === undefined;
  const endpoint = post
    ? `${url}/datasources`
    : `${url}/datasources/${datasource.id}`;

  const backEndRequest = (
    post ? requests.post(endpoint) : requests.put(endpoint)
  )
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
    .send(datasource);

  logger.info(`Pushing to endpoint ${endpoint}`);
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
  const datasourceId = request.params.id;
  if (!datasourceId || datasourceId == 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. datasource Name not supplied',
    });
  }
  const endpoint = `${url}/datasources/${datasourceId}`;
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
