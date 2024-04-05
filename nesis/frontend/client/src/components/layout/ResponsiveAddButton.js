import styled from 'styled-components/macro';
import { ReactComponent as AddIcon } from '../../images/AddIcon.svg';
import { device } from '../../utils/breakpoints';
import SquareButton, { LightSquareButton } from '../inputs/SquareButton';
import React from 'react';

const StyledAddIcon = styled(AddIcon)`
  display: none;
  fill: white;

  @media ${device.tablet} {
    display: inline;
  }
`;

const Text = styled.span`
  display: inline;

  @media ${device.tablet} {
    display: none;
  }
`;

const StyledButton = styled(LightSquareButton)`
  min-width: auto;
`;

function ResponsiveAddButtonWithRef({ children, onClick, style }, ref) {
  return (
    <StyledButton onClick={onClick} ref={ref} style={style}>
      <StyledAddIcon />
      <Text>{children}</Text>
    </StyledButton>
  );
}

export default React.forwardRef(ResponsiveAddButtonWithRef);
