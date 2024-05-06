import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import { ThemeProvider } from 'styled-components/macro';
import theme from './utils/theme';
import { SessionProvider } from './SessionContext';
import { ToasterContextProvider } from './ToasterContext';
import { ConfigContextProvider } from './ConfigContext';

ReactDOM.render(
  <SessionProvider>
    <ToasterContextProvider>
      <ThemeProvider theme={theme}>
        <Router basename={process.env.PUBLIC_URL}>
          <ConfigContextProvider>
            <Route path="/" component={App} />
          </ConfigContextProvider>
        </Router>
      </ThemeProvider>
    </ToasterContextProvider>
  </SessionProvider>,
  document.getElementById('root'),
);
