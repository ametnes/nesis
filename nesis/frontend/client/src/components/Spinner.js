import React from 'react';
import styled from 'styled-components/macro';

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

export const CircleWrapper = styled.div`
  display: inline-block;
  position: relative;
  width: 80px;
  height: 80px;

  & div {
    margin: 0;
    margin-top: 18px;
    width: 50px;
    height: 50px;
    border-width: 6px;
    border-style: solid;
    border-color: #089fdf ${(props) => props.theme.primaryLight}
      ${(props) => props.theme.primaryLight};
    border-image: initial;
    border-radius: 50%;
    animation: 1.2s linear 0s infinite normal none running spinner-rotate;
  }

  @keyframes spinner-rotate {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const Title = styled.div`
  font-weight: 500;
  line-height: 160%;
  text-align: center;
  color: #181c26;
`;

export default function Spinner({ subtitle }) {
  return (
    <Wrapper>
      <SpinnerIcon />
      <Title>Loading...</Title>
      <div>{subtitle}</div>
    </Wrapper>
  );
}

export function SpinnerIcon({ className }) {
  return (
    <CircleWrapper className={className}>
      <div />
    </CircleWrapper>
  );
}
