import React from 'react';
import Tabs, { RouterTab } from '../../components/layout/Tabs';
import { useHistory, Route, Switch, useRouteMatch } from 'react-router-dom';
import { GearFill } from 'react-bootstrap-icons';
import DatasourcesPage from './Datasources/DatasourcesPage';
import UsersPage from './Users/UsersPage';
import RolesPage from './Roles/RolesPage';
import Optim from '../../components/Menu';
import styled from 'styled-components/macro';

const Heading = styled.h1`
  background-image: linear-gradient(to right, #089fdf 21%, #5dd375 100%);
  height: 40px;
  color: #ffffff;
  font-weight: 500;
  font-size: 14px;
  padding-left: 20px;
  align-items: center;
  display: flex;
`;

const SettingsPage = () => {
  const history = useHistory();
  const match = useRouteMatch();
  return (
    <Optim>
      <Heading>
        <GearFill size={25} className="mr-2" /> Settings
      </Heading>
      <Tabs
        defaultActiveKey="/settings/datasources"
        onSelect={(key) => history.push(key)}
      >
        <RouterTab path="/settings/datasources">Datasources</RouterTab>
        <RouterTab path="/settings/users">Users</RouterTab>
        <RouterTab path="/settings/roles">Roles</RouterTab>
      </Tabs>
      <div style={{ padding: 8, marginLeft: 5 }}>
        <Switch>
          <Route
            exact
            path={`${match.path}/datasources/new`}
            component={DatasourcesPage}
          />
          <Route
            exact
            path={`${match.path}/datasources`}
            component={DatasourcesPage}
          />
          <Route exact path={`${match.path}/users/new`} component={UsersPage} />
          <Route
            exact
            path={`${match.path}/users/:id/edit`}
            component={UsersPage}
          />
          <Route exact path={`${match.path}/users`} component={UsersPage} />
          <Route exact path={`${match.path}/roles/new`} component={RolesPage} />
          <Route
            exact
            path={`${match.path}/roles/:id/edit`}
            component={RolesPage}
          />
          <Route exact path={`${match.path}/roles`} component={RolesPage} />
        </Switch>
      </div>
    </Optim>
  );
};

export default SettingsPage;
