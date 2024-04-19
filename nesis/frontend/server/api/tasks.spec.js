const api = require('./tasks');
const config = require('../config');
const sinon = require('sinon');
const { Request } = require('../util/test-util');

describe('Tasks', () => {
  it('can be created', () => {
    const requests = new Request();
    const post = api.post(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
      body: {
        type: 'ingest_datasource',
        parent_id: 'some.id.1',
        definition: { datasource: { id: 'some.id.1' } },
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/tasks`,
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
        type: 'ingest_datasource',
        parent_id: 'some.id.1',
        definition: { datasource: { id: 'some.id.1' } },
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/tasks/some.id`,
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
    const tasks = [
      {
        type: 'ingest_datasource',
        parent_id: 'some.id.1',
        definition: { datasource: { id: 'some.id.1' } },
      },
      {
        type: 'ingest_datasource',
        parent_id: 'some.id.2',
        definition: { datasource: { id: 'some.id.2' } },
      },
    ];

    requests.tasks = tasks;
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/tasks`,
      requests.url,
    );
    sinon.assert.match(args, tasks);
  });

  it('can be retrieved by id', () => {
    const requests = new Request();
    const task = {
      type: 'ingest_datasource',
      parent_id: 'some.id.1',
      definition: { datasource: { id: 'some.id.1' } },
      id: 'some.id',
    };

    requests.taskById = task;
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/tasks/${request.params.id}`,
      requests.url,
    );
    sinon.assert.match(args, task);
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/tasks/${request.params.id}`,
      requests.url,
    );
    sinon.assert.match(args, 'Deleted');
  });
});
