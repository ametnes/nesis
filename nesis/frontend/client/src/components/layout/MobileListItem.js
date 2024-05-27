import React from 'react';
// import styled, { css } from 'styled-components/macro';
import styled from 'styled-components';
// import styled from 'styled-components/macro';
import { css } from 'styled-components';
import useStateToggle from '../../utils/useStateToggle';
import ChevronRight from '../../images/ChevronRight.svg';
// import { ReactComponent as ChevronRight } from '../../images/ChevronRight.svg';
import { device } from '../../utils/breakpoints';
import {
  LightDangerSquareButton,
  LightSquareButton,
} from '../inputs/SquareButton';
import SquareButton from '../inputs/SquareButton';

const Container = styled.div`
  background-color: ${(props) => props.theme.white};
  margin: 18px 0;
  padding: 13px;
  border-radius: 10px;
`;

const ChevronLeft = styled.img`
  fill: ${(props) => props.theme.primary};
  opacity: 0.3;
  transform: rotate(180deg);
  transition: 300ms;

  &.open {
    transform: rotate(90deg);
  }
`;

const MobileMainInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const MobileSubContent = styled.div`
  transition: 400ms;
  max-height: ${(props) =>
    props.$expanded ? `${props.$expandedHeight}px` : 0};
  overflow: hidden;
  transition-timing-function: ease-in-out;
`;

export default function MobileItem({
  mainContent,
  expandContent,
  expandedHeight = 550,
}) {
  const [expanded, toggleExpanded] = useStateToggle();
  return (
    <Container>
      <MobileMainInfo onClick={toggleExpanded}>
        {mainContent}
        <ChevronLeft src={ChevronRight} className={expanded ? 'open' : ''} />
      </MobileMainInfo>
      <MobileSubContent $expanded={expanded} $expandedHeight={expandedHeight}>
        {expandContent}
      </MobileSubContent>
    </Container>
  );
}

export const MobileList = styled.div`
  display: none;
  @media ${device.tablet} {
    display: block;
  }
`;

const baseButtonStyles = css`
  width: 100%;
  font-weight: 600;
  line-height: 160%;
  height: 44px;

  & > svg {
    margin-right: 8px;
  }
`;

export const EditButton = styled(SquareButton)`
  margin-top: 23px;
  ${baseButtonStyles}
`;

export const SubActionButton = styled(LightSquareButton)`
  margin-top: 14px;
  ${baseButtonStyles};
  color: ${(props) => props.theme.secondary};

  & > svg {
    fill: ${(props) => props.theme.secondary};
  }
`;

export const DeleteButton = styled(LightDangerSquareButton)`
  margin-top: 14px;
  ${baseButtonStyles};

  & > svg {
    fill: ${(props) => props.theme.danger2};
  }
`;

export const AttributesTwoColumnsContainer = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  & > * {
    flex: 1;
  }
`;
