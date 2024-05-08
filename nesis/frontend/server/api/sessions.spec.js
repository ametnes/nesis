const api = require('./sessions');
const config = require('../profile');
const sinon = require('sinon');
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
    const post = api.post(requests, config.profile.DEV);
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

    post(request, response);
    sinon.assert.calledWith(statusStab, 400);
    sinon.assert.called(responseStab);
  });
});
