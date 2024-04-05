import React from 'react';
import { Route, Redirect } from 'react-router-dom';

const PrivateRoute = ({ component: Component, session, ...rest }) => (
  <Route
    {...rest}
    render={(props) =>
      session ? <Component {...props} /> : <Redirect to="/signin" />
    }
  />
);

export default PrivateRoute;
