import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import { BrowserRouter as Router, Route } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import theme from './utils/theme';
import { SessionProvider } from './SessionContext';
import { ToasterContextProvider } from './ToasterContext';
import { ConfigContextProvider } from './ConfigContext';
import GoogleContextProvider from './GoogleAuthContext';

const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <SessionProvider>
    <ToasterContextProvider>
      <ThemeProvider theme={theme}>
        <Router basename={process.env.PUBLIC_URL}>
          <ConfigContextProvider>
            <GoogleContextProvider>
              <Route path="/" component={App} />
            </GoogleContextProvider>
          </ConfigContextProvider>
        </Router>
      </ThemeProvider>
    </ToasterContextProvider>
  </SessionProvider>,
);
