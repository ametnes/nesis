import styled from 'styled-components';
import { device } from '../../utils/breakpoints';

const TwoColumnsContent = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: space-between;

  & > *:first-child {
    margin-right: 20px;

    @media ${device.tablet} {
      margin-right: 0;
    }
  }

  @media ${device.tablet} {
    flex-direction: column;
  }
`;

export default TwoColumnsContent;
