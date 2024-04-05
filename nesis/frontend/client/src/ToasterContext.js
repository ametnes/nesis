import React, { useCallback, useContext, useMemo, useState } from 'react';
import PropTypes from 'prop-types';
import { Toast } from 'react-bootstrap';

const ToasterContext = React.createContext({});

ToasterContextProvider.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node,
  ]).isRequired,
};

export default ToasterContext;

const TOAST_CLOSE_TIMEOUT = 5000;

export function ToasterContextProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback(
    function (toastId) {
      setToasts((prev) => prev.filter((t) => t.id !== toastId));
    },
    [setToasts],
  );

  const addToast = useCallback(
    function (toast) {
      const toastWithId = {
        ...toast,
        id: Math.random(),
      };
      setTimeout(() => {
        removeToast(toastWithId.id);
      }, TOAST_CLOSE_TIMEOUT);
      setToasts((prev) => [toastWithId, ...prev]);
    },
    [setToasts, removeToast],
  );

  const value = useMemo(() => ({ addToast }), [addToast]);

  return (
    <ToasterContext.Provider value={value}>
      <div
        style={{
          position: 'absolute',
          top: 32,
          right: 16,
        }}
      >
        {toasts.map((toast) => (
          <Toast key={toast.id} onClose={() => removeToast(toast.id)}>
            <Toast.Header>
              <strong>{toast.title}</strong>
            </Toast.Header>
            <Toast.Body>{toast.content}</Toast.Body>
          </Toast>
        ))}
      </div>
      {children}
    </ToasterContext.Provider>
  );
}

export function useAddToast() {
  const context = useContext(ToasterContext);
  return context && context.addToast;
}
