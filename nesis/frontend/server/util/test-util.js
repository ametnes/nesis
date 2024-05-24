const util = require('./functions');

class Request {
  constructor() {
    this.url = null;
    this.data = null;
    this.method = null;
    this.headers = {};
    this.params = {};
    this.sessions = [];
    this.rules = [];
    this.ruleById = {};
    this.rulesByModel = [];
    this.datasources = [];
    this.datasourceByName = {};
    this.predictions = [];
    this.predictionsByModel = [];
    this.models = [];
    this.dataobjects = [];
    this.tasks = [];
    this.apps = [];
    this.taskById = {};
    this.appById = {};
    this.targets = {};
    this.azureUserData = {};
  }
  set(header, value) {
    this.headers[header] = value;
    return this;
  }
  get(url) {
    this.url = url;
    this.method = 'GET';
    return this;
  }
  query(params) {
    this.params = params;
    return this;
  }
  delete(url) {
    this.url = url;
    this.method = 'DELETE';
    return this;
  }
  post(url) {
    this.url = url;
    this.method = 'POST';
    return this;
  }
  put(url) {
    this.url = url;
    this.method = 'PUT';
    return this;
  }
  then(callback) {
    let res;
    if (this.method === 'POST') {
      if (this.url.endsWith('/rules')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.rules.push(res.body);
      } else if (this.url.endsWith('/predictions')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.predictions.push(res.body);
      } else if (this.url.endsWith('/sessions')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.sessions.push(res.body);
      } else if (this.url.endsWith('/datasources')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.datasources.push(res.body);
      } else if (this.url.endsWith('/models')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.models.push(res.body);
      } else if (this.url.endsWith('/tasks')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.tasks.push(res.body);
      } else if (this.url.endsWith('/apps')) {
        res = {
          body: Object.assign({}, this.data, { id: util.guid() }),
          status: 200,
        };
        this.apps.push(res.body);
      }
    } else if (this.method === 'PUT') {
      if (this.url.includes('/rules/')) {
        res = { body: this.data, status: 200 };
      } else if (this.url.includes('/predictions/')) {
        res = { body: this.data, status: 200 };
      } else if (this.url.includes('/datasources/')) {
        res = { body: this.data, status: 200 };
      } else if (this.url.includes('/tasks/')) {
        res = { body: this.data, status: 200 };
      } else if (this.url.includes('/apps/')) {
        res = { body: this.data, status: 200 };
      }
    } else if (this.method === 'GET') {
      if (this.url.endsWith('/rules')) {
        res = { body: this.rules, status: 200 };
      } else if (this.url.includes('/rules/')) {
        res = { body: this.ruleById, status: 200 };
      } else if (this.url.endsWith('/predictions')) {
        res = { body: this.predictions, status: 200 };
      } else if (this.url.endsWith('/datasources')) {
        res = { body: this.datasources, status: 200 };
      } else if (this.url.includes('/datasources/')) {
        res = { body: this.datasourceByName, status: 200 };
      } else if (this.url.endsWith('/tasks')) {
        res = { body: this.tasks, status: 200 };
      } else if (this.url.endsWith('/apps')) {
        res = { body: this.apps, status: 200 };
      } else if (this.url.includes('/tasks/')) {
        res = { body: this.taskById, status: 200 };
      } else if (this.url.includes('/apps/')) {
        res = { body: this.appById, status: 200 };
      } else if (this.url.endsWith('/v1.0/me')) {
        res = { body: this.azureUserData, status: 200 };
      }
    } else if (this.method === 'DELETE') {
      res = { body: 'Deleted', status: 200 };
    }
    callback(res);
    return this;
  }
  catch(e) {
    /* Ignore */
  }
  send(data) {
    this.data = data;
    return this;
  }
}

module.exports.Request = Request;
