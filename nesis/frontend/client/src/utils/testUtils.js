import React from 'react';
import { createMemoryHistory } from 'history';
import { Router } from 'react-router-dom';
import { render } from '@testing-library/react';
import { ToasterContextProvider } from '../ToasterContext';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ConfigContextProvider } from '../ConfigContext';
import GoogleContextProvider from './GoogleAuthContext';

export function renderWithRouter(
  ui,
  {
    route = '/',
    history = createMemoryHistory({ initialEntries: [route] }),
  } = {}
) {
  const Wrapper = ({ children }) => (
    <Router history={history}>{children}</Router>
  );
  return {
    ...render(ui, { wrapper: Wrapper }),
    history,
  };
}

const queryClient = new QueryClient()

export function renderWithContext(ui, options) {
  return {
    ...renderWithRouter(
      <ToasterContextProvider>
        <ConfigContextProvider>
          <GoogleContextProvider>{ui}</GoogleContextProvider>
        </ConfigContextProvider >
      </ToasterContextProvider>,
      options
    ),
  };
}

export function mockGetImplementation(config) {
  return function get(path) {
    if (config[path]) {
      return Promise.resolve({
        body: config[path],
      });
    } else {
      throw new Error('Unexpected request path=' + path);
    }
  };
}
