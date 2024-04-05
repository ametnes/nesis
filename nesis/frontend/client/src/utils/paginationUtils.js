export function countTotalPages(items, pageSize) {
  if (!items) {
    return 0;
  }
  return Math.ceil(items / pageSize);
}

export function paginateList(
  items,
  activePage,
  pageSize,
  totalCount = items ? items.length : 0,
  sortFn = () => 0,
) {
  items.sort(sortFn);
  return items.slice(
    (activePage - 1) * pageSize,
    Math.min(activePage * pageSize, totalCount),
  );
}

export function reverseSort(sortFn) {
  return function reversedSort(a, b) {
    return -sortFn(a, b);
  };
}

export function getSortFunction(
  sortConfig,
  currentSort,
  defaultSortFn = () => 0,
) {
  if (!currentSort) {
    return defaultSortFn;
  }
  if (!sortConfig[currentSort.field]) {
    return defaultSortFn;
  }
  if (currentSort.direction === SortDirection.DESCENDING) {
    return reverseSort(sortConfig[currentSort.field]);
  }
  return sortConfig[currentSort.field];
}

export const SortDirection = {
  ASCENDING: 'ASCENDING',
  DESCENDING: 'DESCENDING',
};
