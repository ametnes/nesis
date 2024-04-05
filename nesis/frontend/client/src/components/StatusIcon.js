import React from 'react';
import styled from 'styled-components/macro';

const Main = styled.span`
  margin-right: 4px;
  color: ${(props) => (props.$enabled ? '#1EB648' : '#D14949')};
`;

export default function StatusIcon({ status }) {
  return <Main $enabled={status}>&#9679;</Main>;
}
