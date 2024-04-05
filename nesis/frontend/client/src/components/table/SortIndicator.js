import React from 'react';
import styled from 'styled-components/macro';
import { ReactComponent as Ascending } from './Ascending.svg';
import { ReactComponent as Descending } from './Descending.svg';
import { ReactComponent as NoSortedBy } from './NoSortedBy.svg';
import { SortDirection } from '../../utils/paginationUtils';

const Main = styled.button`
  border: none;
  background: none;
  cursor: pointer;
  margin-left: 6px;
`;

export default function SortIndicator({
  onSortChange,
  fieldName,
  currentSort,
}) {
  function handleClick() {
    if (!currentSort || currentSort.field !== fieldName) {
      onSortChange({
        field: fieldName,
        direction: SortDirection.ASCENDING,
      });
    } else if (currentSort.direction === SortDirection.ASCENDING) {
      onSortChange({
        field: fieldName,
        direction: SortDirection.DESCENDING,
      });
    } else {
      onSortChange(null);
    }
  }

  let sortIcon = <Descending title="Descending" />;

  if (!currentSort || currentSort.field !== fieldName) {
    sortIcon = <NoSortedBy title="Not Sorted By" />;
  } else if (currentSort.direction === SortDirection.ASCENDING) {
    sortIcon = <Ascending title="Ascending" />;
  }
  return <Main onClick={handleClick}>{sortIcon}</Main>;
}
