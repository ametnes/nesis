import styled from 'styled-components';
import './App.css';
import { Route, Switch } from 'react-router-dom';
import SignInPage from './pages/SignInPage';
import Highcharts from 'highcharts';
import { useCurrentSession } from './SessionContext';
import PrivateRoute from './PrivateRoute.js';
import SettingsPage from './pages/Settings/SettingPage.js';
import ChatPage from './pages/DocumentGPT/ChatPage.js';

import 'highcharts/css/highcharts.css';
require('highcharts/modules/exporting')(Highcharts);

const AppContainer = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
`;

function MainContainer() {
  const session = useCurrentSession();

  return (
    <AppContainer>
      <Switch>
        <Route path="/" exact component={SignInPage} />
        <Route path="/signin" exact component={SignInPage} />
        <PrivateRoute
          path="/settings"
          component={SettingsPage}
          session={session}
        />
        <PrivateRoute
          path="/discovery/documents"
          component={ChatPage}
          session={session}
        />
      </Switch>
    </AppContainer>
  );
}

export default MainContainer;
