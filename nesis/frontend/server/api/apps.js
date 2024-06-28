const logger = require('../util/logger');

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const endpoint = `${url}/apps`;
  logger.info(`Getting apps endpoint ${endpoint}`);
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
  const appId = request.params.id;
  if (!appId) {
    return response.status(400).send({
      message: 'Invalid request. App id not supplied',
    });
  }
  const endpoint = `${url}/apps/${appId}`;
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
  const app = request.body;
  if (!app) {
    return response.status(400).send({
      message: 'Invalid request. App not supplied',
    });
  }

  const endpoint = app.id ? `${url}/apps/${app.id}` : `${url}/apps`;

  logger.info(`Posting endpoint ${endpoint}`);

  const post = app.id === null || app.id === undefined;
  const backEndRequest = (
    post ? requests.post(endpoint) : requests.put(endpoint)
  )
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json');
  if (request.headers && request.headers.authorization) {
    backEndRequest.set('Authorization', request.headers.authorization);
  }

  backEndRequest
    .send(app)
    .then((res) => {
      console.log(JSON.stringify(res));
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

const getRoles = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const appId = request.params.id;
  if (!appId || appId == undefined || appId === 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. Role name not supplied',
    });
  }
  const endpoint = `${url}/apps/${appId}/roles`;
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

const _delete = (requests, profile) => (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const appId = request.params.id;
  if (!appId || appId == 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. app Name not supplied',
    });
  }
  const endpoint = `${url}/apps/${appId}`;
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
  getRoles: getRoles,
};
