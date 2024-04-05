import request from 'superagent';
import { getToken } from './tokenStorage';

class Client {
  constructor(url, signOut = () => undefined) {
    this.url = url;
    this.client = request;
    this.signOut = signOut;
  }

  post(endpoint, data, callback) {
    const request = this.client
      .post(`${this.url}/${endpoint}`)
      .send(data)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json');
    appendAuthHeader(request);

    return toPromise(request, callback, this.signOut);
  }

  put(endpoint, data, callback) {
    const request = this.client
      .put(`${this.url}/${endpoint}`)
      .send(data)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json');
    appendAuthHeader(request);

    return toPromise(request, callback, this.signOut);
  }

  delete(endpoint, query, callback) {
    const request = this.client
      .delete(`${this.url}/${endpoint}`)
      .query(query)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json');
    appendAuthHeader(request);

    return toPromise(request, callback, this.signOut);
  }

  get(endpoint, params, callback) {
    const request = this.client
      .get(`${this.url}/${endpoint}`)
      .set('Accept', 'application/json')
      .set('Content-Type', 'application/json')
      .query(params);

    appendAuthHeader(request);

    return toPromise(request, callback, this.signOut);
  }

  putUser(user, callback) {
    return this.put(user.id ? `users/${user.id}` : 'users', user, callback);
  }
}

function toPromise(request, callback, signOut) {
  return new Promise((resolve, reject) => {
    request.end((err, res) => {
      if (callback) {
        callback(err, res);
      }
      if (err) {
        if (signOut && err.response && err.response.status === 401) {
          signOut();
        }
        reject(err);
      } else {
        resolve(res);
      }
    });
  });
}

function appendAuthHeader(request) {
  const token = getToken();
  if (token) {
    request.set('Authorization', `Bearer ${token}`);
  }
}

export { Client };
// local
export const API_PREFIX = `/api`;
//deployment
// export const API_PREFIX = `/optim/api`;
const client = new Client(API_PREFIX);
export default client;
