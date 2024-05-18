const express = require('express');
const path = require('path');
const cors = require('cors');
const requests = require('superagent');

const logger = require('./util/logger');
const api = require('./api/index');

const app = express();
const config = require('./profile');
const profile = config.profile[process.env.PROFILE] || config.profile.DEV;
//Handles post requests
const bodyParser = require('body-parser');
async function init() {
  app.use(bodyParser.json());
  app.use(bodyParser.urlencoded({ extended: true }));
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));
  app.use(cors());

  const home = process.env.APP_HOME || path.join(__dirname, '../client/build');
  logger.info(`Running server from ${home}`);
  app.use(express.static(home));

  const API = {
    SESSIONS: '/api/sessions',
    SETTINGS: '/api/:module/settings',
    ROLES: '/api/roles',
    USERS: '/api/users',
    TASKS: '/api/tasks',
    DATA_SOURCES: '/api/datasources',
    CONFIG: '/api/config',
    QANDA_PREDICTIONS: '/api/qanda/predictions',
  };

  //Session
  app.post(API.SESSIONS, api.sessions.post(requests, profile));
  app.delete(
    API.SESSIONS,
    api.sessions.delete(requests, profile.SERVICE_ENDPOINT),
  );

  //Settings
  app.get(`${API.SETTINGS}/:id`, api.settings.getById(requests, profile));
  app.get(API.SETTINGS, api.settings.getAll(requests, profile));
  app.post(API.SETTINGS, api.settings.post(requests, profile));
  app.delete(`${API.SETTINGS}/:id`, api.settings.delete(requests, profile));

  //Roles
  app.get(`${API.ROLES}/:id`, api.roles.getById(requests, profile));
  app.get(API.ROLES, api.roles.getAll(requests, profile));
  app.post(API.ROLES, api.roles.post(requests, profile));
  app.delete(`${API.ROLES}/:id`, api.settings.delete(requests, profile));

  //Users
  app.get(`${API.USERS}/:id`, api.users.getById(requests, profile));
  app.get(`${API.USERS}/:id/roles`, api.users.getRoles(requests, profile));
  app.get(API.USERS, api.users.getAll(requests, profile));
  app.post(API.USERS, api.users.post(requests, profile));
  app.delete(`${API.USERS}/:id`, api.users.delete(requests, profile));

  //Tasks
  app.get(`${API.TASKS}/:id`, api.tasks.getById(requests, profile));
  app.get(API.TASKS, api.tasks.getAll(requests, profile));
  app.post(API.TASKS, api.tasks.post(requests, profile));
  app.delete(`${API.TASKS}/:id`, api.tasks.delete(requests, profile));

  //Data source
  app.get(
    `${API.DATA_SOURCES}/:id`,
    api.datasources.getById(requests, profile),
  );
  app.get(API.DATA_SOURCES, api.datasources.getAll(requests, profile));
  app.post(API.DATA_SOURCES, api.datasources.post(requests, profile));
  app.delete(
    `${API.DATA_SOURCES}/:id`,
    api.datasources.delete(requests, profile),
  );

  /* Qanda chatbot */
  app.post(
    `${API.QANDA_PREDICTIONS}`,
    api.qanda_predictions.post(requests, profile),
  );
  app.get(
    `${API.QANDA_PREDICTIONS}`,
    api.qanda_predictions.getAll(requests, profile),
  );
  app.get(
    `${API.QANDA_PREDICTIONS}/:id`,
    api.qanda_predictions.getById(requests, profile),
  );
  app.get(`${API.CONFIG}`, api.config.get(requests, profile));

  app.get('/*', (req, res) => {
    res.sendFile(path.join(home, 'index.html'));
  });

  const port = 8000;
  app.listen(port, function () {
    logger.info(`App is listening on port ${port}`);
  });
}

init().catch((e) => {
  console.error(e);
  logger.error(`Could not start server ${JSON.stringify(e)}`);
});
