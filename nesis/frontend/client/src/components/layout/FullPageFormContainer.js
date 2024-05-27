// import styled from 'styled-components/macro';
import styled from 'styled-components';
import { device } from '../../utils/breakpoints';

const FullPageFormContainer = styled.div`
  margin: auto;
  position: relative;
  text-align: center;
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  padding: 0;
  width: 40%;

  @media ${device.phoneWide} {
    padding: 0 32px;
    width: 100%;
  }

  @media ${device.tablet} {
    padding: 0;
    width: 70%;
  }
`;

export default FullPageFormContainer;
