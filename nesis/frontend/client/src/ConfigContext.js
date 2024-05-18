import React, { useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import useClient from './utils/useClient';

const ConfigContext = React.createContext({});

ConfigContextProvider.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]).isRequired,
};

export default ConfigContext;

export function ConfigContextProvider({ children }) {
  const client = useClient();
  const [config, setConfig] = useState(null);
  useEffect(() => {
    client.get('config').then((res) => {
      setConfig(JSON.parse(res.text));
    });
  }, [setConfig, client]);
  return (
    <ConfigContext.Provider value={config}>{children}</ConfigContext.Provider>
  );
}

export function useConfig() {
  return useContext(ConfigContext);
}
