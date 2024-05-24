const api = require('./apps');
const config = require('../profile');
const sinon = require('sinon');
const { Request } = require('../util/test-util');

describe('Apps', () => {
  it('can be created', () => {
    const requests = new Request();
    const post = api.post(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
      body: {
        name: 'app name',
        description: 'app description',
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    post(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);
    const args = responseStab.getCall(0).args[0];
    sinon.assert.match(args, request.body);
    sinon.assert.match(
      `${config.profile.DEV.SERVICE_ENDPOINT}/apps`,
      requests.url,
    );
    sinon.assert.match('POST', requests.method);
    sinon.assert.match(
      request.headers.authorization,
      requests.headers['Authorization'],
    );
  });

  it('can be updated', () => {
    const requests = new Request();
    const post = api.post(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
      body: {
        name: 'app name',
        description: 'app description',
        id: 'some.id',
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    post(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);
    const args = responseStab.getCall(0).args[0];
    sinon.assert.match(args, request.body);
    sinon.assert.match(
      `${config.profile.DEV.SERVICE_ENDPOINT}/apps/some.id`,
      requests.url,
    );
    sinon.assert.match('PUT', requests.method);
    sinon.assert.match(
      request.headers.authorization,
      requests.headers['Authorization'],
    );
  });

  it('can be retrieved', () => {
    const requests = new Request();
    const apps = [
      {
        name: 'app name-1',
        description: 'app description',
      },
      {
        name: 'app name-2',
        description: 'app description',
      },
    ];

    requests.apps = apps;
    const getAll = api.getAll(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    getAll(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);
    const args = responseStab.getCall(0).args[0];
    sinon.assert.match(
      `${config.profile.DEV.SERVICE_ENDPOINT}/apps`,
      requests.url,
    );
    sinon.assert.match(args, apps);
  });

  it('can be retrieved by id', () => {
    const requests = new Request();
    const app = {
      name: 'app name',
      description: 'app description',
    };

    requests.appById = app;
    const getById = api.getById(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
      params: {
        id: '123456789',
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    getById(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);
    const args = responseStab.getCall(0).args[0];
    sinon.assert.match(
      `${config.profile.DEV.SERVICE_ENDPOINT}/apps/${request.params.id}`,
      requests.url,
    );
    sinon.assert.match(args, app);
  });

  it('can be deleted', () => {
    const requests = new Request();
    const targets = [
      {
        name: 'test',
        engine: 'sqlserver',
      },
    ];

    requests.targets = targets;
    const _delete = api.delete(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
      params: {
        id: '123456789',
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    _delete(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);
    const args = responseStab.getCall(0).args[0];
    sinon.assert.match(
      `${config.profile.DEV.SERVICE_ENDPOINT}/apps/${request.params.id}`,
      requests.url,
    );
    sinon.assert.match(args, 'Deleted');
  });
});
