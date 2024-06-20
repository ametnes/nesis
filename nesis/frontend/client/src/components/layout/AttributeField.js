import styled from 'styled-components';
import React from 'react';

const ResourceFieldTitle = styled.div`
  color: ${(props) => props.theme.dark};
  font-weight: 600;
  line-height: 160%;
  margin-top: 14px;
`;

const ResourceContent = styled.div`
  color: ${(props) => props.theme.dark};
  line-height: 160%;
`;

export default function AttributeField({ title, children }) {
  return (
    <div>
      <ResourceFieldTitle>{title}</ResourceFieldTitle>
      <ResourceContent>{children}</ResourceContent>
    </div>
  );
}
