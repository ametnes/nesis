import styled from 'styled-components/macro';
import { device } from '../../utils/breakpoints';

const FormRow = styled.span`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-top: 11px;

  @media ${device.tablet} {
    flex-direction: column;
  }

  & > * {
    @media ${device.tablet} {
      width: 100%;
    }
  }

  & > *:not(:last-child) {
    margin-right: 32px;
    flex: 18;
  }
`;

export default FormRow;

export const Column = styled.div`
  flex: 1;
`;
