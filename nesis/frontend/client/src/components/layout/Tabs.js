import React from 'react';
// import styled from 'styled-components/macro';
import styled from 'styled-components';
import { useHistory, matchPath } from 'react-router-dom';

const Main = styled.div`
  border-bottom: 1px solid rgba(5, 36, 117, 0.1);
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  margin-bottom: 0px;
`;

const TabButton = styled.button`
  font-weight: 500;
  background: none;
  border: none;
  padding: 8px 16px;
  color: ${(props) => (props.$active ? '#089FDF' : props.theme.secondary)};
  opacity: ${(props) => (props.$active ? 1 : 0.4)};
  border-bottom: ${(props) => (props.$active ? 2 : 0)}px solid
    ${(props) => (props.$active ? '#089FDF' : '#DBDBDB')};
  &:focus {
    outline: none;
  }
`;

export default function Tabs({ children, className }) {
  return <Main className={className}>{children}</Main>;
}

export function Tab({ children, onClick, active, className }) {
  return (
    <TabButton $active={active} onClick={onClick} className={className}>
      {children}
    </TabButton>
  );
}

export function RouterTab({ children, path, subPaths = [] }) {
  const history = useHistory();
  let active = matchPath(history.location.pathname, {
    path,
    exact: true,
    strict: false,
  });
  if (!active) {
    active = subPaths.some((subPath) =>
      matchPath(history.location.pathname, {
        path: subPath,
        exact: true,
        strict: true,
      }),
    );
  }
  return (
    <TabButton $active={active} onClick={() => history.push(path)}>
      {children}
    </TabButton>
  );
}
