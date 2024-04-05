import React from 'react';
import SquareButton, { LightSquareButton } from './inputs/SquareButton';
import styled from 'styled-components/macro';
import { device } from '../utils/breakpoints';

const Container = styled.div`
  width: 100%;
  display: flex;
  justify-content: ${(props) => (props.$centered ? 'center' : 'space-between')};
  margin-top: 26px;
  // TODO remove when formControl is removed
  margin-left: ${(props) => (props.$centered ? '0' : '15px')};

  @media ${device.tablet} {
    margin-left: 0;
  }
`;

const MainControls = styled.div`
  display: flex;
  width: 100%;

  @media ${device.tablet} {
    flex-direction: column;
  }

  & > *:first-child {
    margin-right: 16px;

    @media ${device.tablet} {
      margin-right: 0;
      margin-bottom: 16px;
    }
  }
`;

const CancelButton = styled(SquareButton)`
  background-color: ${(props) => props.theme.primaryLight};
  color: ${(props) => props.theme.black};
`;

export default function FormControls({
  submitTitle = 'Submit',
  onCancel,
  submitDisabled,
  onDelete,
  centered,
  additionalControls,
  submitTooltip,
  className,
}) {
  return (
    <Container $centered={centered} className={className}>
      <MainControls>
        <LightSquareButton
          type="submit"
          disabled={submitDisabled}
          title={submitTooltip}
        >
          {submitTitle}
        </LightSquareButton>{' '}
        <CancelButton type="button" onClick={onCancel} variant="light">
          Cancel
        </CancelButton>
      </MainControls>
      {additionalControls}
    </Container>
  );
}
