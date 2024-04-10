const api = require('./datasources');
const config = require('../config');
const sinon = require('sinon');
const { Request } = require('../util/test-util');

describe('Datasources', () => {
  it('can be created', () => {
    const requests = new Request();
    const post = api.post(requests, config.profile.DEV);
    const request = {
      headers: {
        authorization: 'Usdz3323233eeewe',
      },
      body: {
        name: 'Test',
        engine: 'sqlserver',
        dataobjects: 'customer',
        connection: {
          host: 'host.name',
          user: 'user',
          password: 'password',
        },
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/datasources`,
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
        id: '89lio',
        name: 'Test',
        engine: 'sqlserver',
        dataobjects: 'customer',
        connection: {
          host: 'host.name',
          user: 'user',
          password: 'password',
        },
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/datasources/89lio`,
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
    const datasources = [
      {
        name: 'Test',
        engine: 'sqlserver',
        dataobjects: 'customer',
        connection: {
          host: 'host.name',
          user: 'user',
          password: 'password',
        },
      },
      {
        name: 'Test',
        engine: 'sqlserver',
        dataobjects: 'customer',
        connection: {
          host: 'host.name',
          user: 'user',
          password: 'password',
        },
      },
    ];

    requests.datasources = datasources;
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/datasources`,
      requests.url,
    );
    sinon.assert.match(args, datasources);
  });

  it('can be retrieved by id', () => {
    const requests = new Request();
    const datasource = {
      name: 'Test',
      engine: 'sqlserver',
      dataobjects: [
        {
          name: 'customer',
        },
      ],
    };

    requests.datasourceByName = datasource;
    const getByName = api.getById(requests, config.profile.DEV);
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

    getByName(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);
    const args = responseStab.getCall(0).args[0];
    sinon.assert.match(
      `${config.profile.DEV.SERVICE_ENDPOINT}/datasources/${request.params.id}`,
      requests.url,
    );
    sinon.assert.match(args, datasource);
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/datasources/${request.params.id}`,
      requests.url,
    );
    sinon.assert.match(args, 'Deleted');
  });
});
