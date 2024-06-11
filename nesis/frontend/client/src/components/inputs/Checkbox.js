import React from 'react';
import styled from 'styled-components';

const Wrapper = styled.div`
  display: flex;
  align-items: center;
  margin-top: 8px;
`;

const StyledInput = styled.input`
  border: 2px solid
    ${(props) =>
      props.$hasError ? props.theme.error : 'rgba(51, 104, 242, 0.1)'};
  box-sizing: border-box;
  border-radius: 5px;

  &:focus {
    border-color: ${(props) => props.theme.tertiary};
  }

  &:checked {
    background: ${(props) => props.theme.primary};
  }

  &:checked + label:before {
    // position: absolute;
    content: '✔';
    font-family: ${(props) => props.theme.mainFont};
    color: ${(props) => props.theme.white};
    display: inline-block;
    margin-left: -32px;
    padding: 0 10px;
  }

  height: 20px;
  width: 20px;
  -webkit-appearance: none;
`;

const LabelOnTopOfInput = styled.label`
  margin: 0 0 0 6px;
  color: ${(props) => props.theme.dark};
  background: ${(props) => props.theme.white};
`;

export default function Checkbox({
  label,
  value,
  onChange,
  id,
  name,
  onBlur,
  onKeyDown,
  hasError,
}) {
  return (
    <Wrapper>
      <StyledInput
        type="checkbox"
        checked={!!value}
        value={!!value}
        onChange={(...args) => {
          onChange(...args);
        }}
        id={id}
        name={name}
        onKeyDown={onKeyDown}
        onBlur={onBlur}
        $hasError={hasError}
      />
      {label && <LabelOnTopOfInput htmlFor={id}>{label}</LabelOnTopOfInput>}
    </Wrapper>
  );
}
