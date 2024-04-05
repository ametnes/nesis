import styled from 'styled-components/macro';
import { ReactComponent as ChevronRight } from '../images/ChevronRight.svg';
import React, { useMemo, useRef, useState } from 'react';
import { countTotalPages, paginateList } from '../utils/paginationUtils';
import { device } from '../utils/breakpoints';
import useOnClickOutside from '../utils/useOnClickOutside';

const ADDITIONAL_PAGES_TO_SHOW = 1;

const Pagination = styled.div`
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 18px;

  @media ${device.tablet} {
    justify-content: space-between;
  }
`;

const PaginationButton = styled.button`
  background: ${(props) => (props.$active ? '#089fdf' : 'none')};
  color: ${(props) => (props.$active ? props.theme.black : '#089fdf')};
  cursor: pointer;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  outline: none;
  padding: 0;
  font-weight: 400;

  &:disabled {
    opacity: 0.3;
    cursor: default;
  }

  @media ${device.tablet} {
    border: 1px solid ${(props) => props.theme.primary};
    border-radius: 3px;
    width: 86px;
    height: 36px;

    font-weight: 500;
    line-height: 19px;
    padding: 0 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
`;

const MobileButtonText = styled.span`
  display: none;

  @media ${device.tablet} {
    display: inline;
    margin: 0 8px;
  }
`;

const ChevronLeftBlue = styled(ChevronRight)`
  transform: rotate(180deg);
  fill: ${(props) => props.theme.primary};
`;

const ChevronRightBlue = styled(ChevronRight)`
  fill: ${(props) => props.theme.primary};
`;

const ChevronDownWhite = styled(ChevronRight)`
  transform: rotate(90deg);
  fill: ${(props) => props.theme.white};
`;

const DesktopOnlyPaginationButton = styled(PaginationButton)`
  @media ${device.tablet} {
    display: none;
  }
`;

const PagesDropdown = styled.div`
  display: none;
  position: relative;
  @media ${device.tablet} {
    display: flex;
  }
  background: #089fdf;
  color: ${(props) => props.theme.black};
  border-radius: 3px;
  width: 86px;
  height: 36px;
  font-weight: 500;
  line-height: 19px;
  padding: 0 12px;
  align-items: center;
  justify-content: space-between;
`;

const DropdownButton = styled(PaginationButton)`
  background: ${(props) => props.theme.white};
`;

const buttonHeight = 36;

const DropdownContent = styled.div`
  position: absolute;
  top: -${(props) => props.$items * buttonHeight + 1}px;
  left: 0;
`;

export default function PaginationRow({ pages, active, onActiveChange }) {
  const dropdownRef = useRef(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  useOnClickOutside(dropdownRef, () => setDropdownOpen(false));

  if (!pages || pages < 2) {
    return null;
  }
  const items = [];
  const mobileItems = [];
  const startingPage =
    active - ADDITIONAL_PAGES_TO_SHOW > 0
      ? active - ADDITIONAL_PAGES_TO_SHOW
      : 1;
  const endingPage =
    active + ADDITIONAL_PAGES_TO_SHOW < pages
      ? active + ADDITIONAL_PAGES_TO_SHOW
      : pages;
  for (let number = startingPage; number <= endingPage; number++) {
    items.push(
      <DesktopOnlyPaginationButton
        key={number}
        $active={number === active}
        onClick={() => onActiveChange(number)}
      >
        {number}
      </DesktopOnlyPaginationButton>,
    );
  }

  for (let currentPage = 0; currentPage <= pages; currentPage++) {
    if (currentPage !== active) {
      mobileItems.push(
        <DropdownButton
          key={currentPage}
          onClick={() => onActiveChange(currentPage)}
        >
          {currentPage}
        </DropdownButton>,
      );
    }
  }

  return (
    <Pagination>
      <PaginationButton
        onClick={() => onActiveChange(active - 1)}
        disabled={active <= 1}
        title="Previous Page"
      >
        <ChevronLeftBlue />
        <MobileButtonText>Prev</MobileButtonText>
      </PaginationButton>
      {items}
      <PagesDropdown
        ref={dropdownRef}
        onClick={() => setDropdownOpen((prev) => !prev)}
      >
        {active}
        <ChevronDownWhite />
        {dropdownOpen && (
          <DropdownContent $items={pages}>{mobileItems}</DropdownContent>
        )}
      </PagesDropdown>
      <PaginationButton
        title="Next Page"
        onClick={() => onActiveChange(active + 1)}
        disabled={active === pages}
      >
        <MobileButtonText>Next</MobileButtonText>
        <ChevronRightBlue />
      </PaginationButton>
    </Pagination>
  );
}

const DEFAULT_PAGE_SIZE = 10;

export function usePagination(
  items,
  searchText,
  filter,
  pageSize = DEFAULT_PAGE_SIZE,
) {
  const totalPages = countTotalPages(items?.length || 0, pageSize);
  const [activePage, setActivePage] = useState(1);

  React.useEffect(() => {
    setActivePage(1);
  }, [searchText, filter]);

  const paginatedItems = useMemo(
    () => paginateList(items, activePage, pageSize, items?.length),
    [items, activePage, pageSize],
  );

  return [
    paginatedItems,
    <>
      {totalPages > 1 && (
        <PaginationRow
          pages={totalPages}
          active={activePage}
          onActiveChange={setActivePage}
        />
      )}
    </>,
  ];
}
