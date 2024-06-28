import React from 'react';
import styled from 'styled-components';
import Spinner from './Spinner';
import SortIndicator from './table/SortIndicator';
import { ReactComponent as BinIcon } from '../images/BinIcon.svg';

const StyledTable = styled.table`
  background: ${(props) => props.theme.white};
  border-radius: 10px;
  width: 100%;
  line-height: 160%;

  & td {
    color: #515151;
  }

  & td,
  th {
    padding: 10px;
    white-space: nowrap;
  }

  & td.no-wrap {
    white-space: nowrap;
  }

  & thead {
    // border-bottom: 2px solid rgba(5, 36, 117, 0.1);
  }
`;

export const IconButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  margin-left: 16px;

  fill: ${(props) => props.theme.primaryLight};

  &:hover > svg {
    fill: ${(props) => props.theme.secondaryLight};
  }
`;

const DeleteButtonContainer = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  margin-left: 8px;
  margin-right: 8px;

  fill: ${(props) => props.theme.danger2};

  &:hover > svg {
    fill: ${(props) => props.theme.danger2};
  }
`;

export function DeleteItemButton({ onClick }) {
  return (
    <DeleteButtonContainer title="Delete" onClick={onClick}>
      <BinIcon />
    </DeleteButtonContainer>
  );
}

export const NotificationIconButton = styled.button`
  background: none;
  border: none;
  cursor: pointer;
  margin-left: 16px;
  position: relative;

  fill: ${(props) => props.theme.primaryLight};

  &:hover > svg {
    fill: ${(props) => props.theme.secondaryLight};
  }
`;

const StyledLoadingColumn = styled.th`
  height: 300px;
`;

const SpinnerWrapper = styled.span`
  width: 100%;
  display: flex;
  justify-content: center;
`;

export default function Table({
  className,
  children,
  loading,
  config,
  columns = 1,
  setCurrentSort,
  currentSort,
}) {
  return (
    <StyledTable className={className}>
      {children}
      {config && (
        <TableHeading
          config={config}
          setCurrentSort={setCurrentSort}
          currentSort={currentSort}
        />
      )}
      {loading && (
        <tbody>
          <tr>
            <StyledLoadingColumn colSpan={columns}>
              <SpinnerWrapper>
                <Spinner />
              </SpinnerWrapper>
            </StyledLoadingColumn>
          </tr>
        </tbody>
      )}
    </StyledTable>
  );
}

function TableHeading({ config, setCurrentSort, currentSort }) {
  const { columns } = config;
  return (
    <thead>
      <tr>
        {columns.map((col) => (
          <th key={col.fieldName}>
            {col.name}{' '}
            {col.sortable && (
              <SortIndicator
                fieldName={col.fieldName}
                onSortChange={setCurrentSort}
                currentSort={currentSort}
              />
            )}
          </th>
        ))}
      </tr>
    </thead>
  );
}
