const logger = require('../util/logger');

const getAll = (requests, profile) => async (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const endpoint = `${url}/tasks`;
  logger.info(`Getting tasks endpoint ${endpoint}`);
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
  const taskId = request.params.id;
  if (!taskId) {
    return response.status(400).send({
      message: 'Invalid request. Task name not supplied',
    });
  }
  const endpoint = `${url}/tasks/${taskId}`;
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
  const task = request.body;
  if (!task) {
    return response.status(400).send({
      message: 'Invalid request. Task not supplied',
    });
  }

  const endpoint = task.id ? `${url}/tasks/${task.id}` : `${url}/tasks`;

  logger.info(`Posting endpoint ${endpoint}`);

  const post = task.id === null || task.id === undefined;
  const backEndRequest = (
    post ? requests.post(endpoint) : requests.put(endpoint)
  )
    .set('Accept', 'application/json')
    .set('Content-Type', 'application/json');
  if (request.headers && request.headers.authorization) {
    backEndRequest.set('Authorization', request.headers.authorization);
  }

  backEndRequest
    .send(task)
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

const _delete = (requests, profile) => (request, response) => {
  const url = profile.SERVICE_ENDPOINT;
  const taskId = request.params.id;
  if (!taskId || taskId == 'undefined') {
    return response.status(400).send({
      message: 'Invalid request. task Name not supplied',
    });
  }
  const endpoint = `${url}/tasks/${taskId}`;
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
