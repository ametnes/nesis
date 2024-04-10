import styled from 'styled-components/macro';

const SquareButton = styled.button`
  color: ${(props) => props.theme.white};
  background-color: #089fdf;
  padding: 4px 15px;
  border-radius: 3px;
  text-decoration: none;
  font-weight: 500;
  line-height: 19px;
  text-align: center;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  min-width: 140px;
  min-height: 30px;
  box-sizing: border-box;
  border: none;

  // &:hover {
  //   background-color: ${(props) => props.theme.primaryDark};
  //   color: ${(props) => props.theme.white};
  // }

  &:focus {
    outline: none;
  }

  &:disabled {
    opacity: 50%;
    cursor: not-allowed;
  }
`;

export const LightSquareButton = styled(SquareButton)`
  color: #ffffff;
  background-color: #089fdf;

  &:hover {
    color: #ffffff;
    background-color: #089fdf;
  }
`;

export const DangerSquareButton = styled(SquareButton)`
  color: ${(props) => props.theme.white};
  background-color: ${(props) => props.theme.danger};

  &:hover {
    background-color: ${(props) => props.theme.dangerDark};
  }
`;

export const LightDangerSquareButton = styled(SquareButton)`
  color: ${(props) => props.theme.danger2};
  background-color: rgba(209, 73, 73, 0.05);

  &:hover {
    background-color: ${(props) => props.theme.dangerDark};
    color: ${(props) => props.theme.white};
  }
`;

export const OutlinedSquareButton = styled(SquareButton)`
  color: #089fdf;
  background: none;
  border: 2px solid #089fdf;
  border-radius: 3px;
  font-weight: 600;

  &:hover {
    background: none;
    color: #089fdf;
    border-color: #089fdf;
  }
`;

export const EditOutlinedSquareButton = styled(OutlinedSquareButton)`
  min-width: 50px;
  margin-left: 8px;
  margin-right: 8px;
`;

export default SquareButton;
