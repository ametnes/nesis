const api = require('./sessions');
const config = require('../profile');
const sinon = require('sinon');
const assert = require('chai').assert;
const { Request } = require('../util/test-util');

describe('Sessions', () => {
  it('can be created', () => {
    const requests = new Request();
    const post = api.post(requests, config.profile.DEV);
    const request = {
      headers: {},
      body: {
        email: 'email@domain.com',
        password: 'password',
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
      `${config.profile.DEV.SERVICE_ENDPOINT}/sessions`,
      requests.url,
    );
    sinon.assert.match('POST', requests.method);
  });

  it('can not be created with token key in payload', () => {
    const requests = new Request();
    const request = {
      headers: {},
      body: {
        email: 'email@domain.com',
        [config.profile.DEV.NESIS_OAUTH_TOKEN_KEY]:
          'some.one.knows.something.about.our.internals',
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    const post = api.post(requests, config.profile.DEV);
    post(request, response);
    sinon.assert.calledWith(statusStab, 400);
    sinon.assert.called(responseStab);
  });

  it('can not be created with no payload', () => {
    const requests = new Request();
    const request = {
      headers: {},
      body: null,
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    const post = api.post(requests, config.profile.DEV);
    post(request, response);
    sinon.assert.calledWith(statusStab, 400);
    sinon.assert.called(responseStab);
  });

  it('can be created with Azure', () => {
    const requests = new Request();
    requests.azureUserData = {
      displayName: 'Michy Tan',
      mail: 'michy.tan@acme.onmicrosoft.com',
      userPrincipalName: 'michy.tan@acme.onmicrosoft.com',
    };
    const request = {
      headers: {},
      body: {
        email: 'michy.tan@acme.onmicrosoft.com',
        azure: {
          authority: 'https://login.microsoftonline.com/common/',
          uniqueId: '9cdd0b94-0000-48db-8bc8-00000000',
          tenantId: '041e34c2-0000-44b0-8aa4-00000000',
          accessToken: 'some.key',
          account: {
            username: 'michy.tan@acme.onmicrosoft.com',
            name: 'First Last',
          },
        },
      },
    };

    const responseStab = sinon.stub();
    const statusStab = sinon.stub().returns({ send: responseStab });
    const response = {
      status: statusStab,
    };

    const post = api.post(requests, config.profile.DEV);
    post(request, response);
    sinon.assert.calledWith(statusStab, 200);
    sinon.assert.called(responseStab);

    assert.deepEqual(requests.data, {
      email: 'michy.tan@acme.onmicrosoft.com',
      name: 'First Last',
      ___nesis_oauth_token_key___: '___nesis_oauth_token_value___',
    });
  });
});
