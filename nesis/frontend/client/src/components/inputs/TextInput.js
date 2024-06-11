import React from 'react';
import styled, { css } from 'styled-components';

export const LabelPosition = {
  ON_INPUT_BORDER: 'ON_INPUT_BORDER',
  ON_TOP_OF_INPUT: 'ON_TOP_OF_INPUT',
};

export const TextInputPresentation = {
  SQUARE: 'SQUARE',
  ROUNDED: 'ROUNDED',
};

export const TextInputSize = {
  LARGE: 'LARGE',
  MEDIUM: 'MEDIUM',
};

const baseStyles = css`
  border: 2px solid
    ${(props) => (props.$hasError ? props.theme.error : '#3368f21a')};
  background: none;
  box-sizing: border-box;
  border-radius: ${(props) =>
    props.$presentation === TextInputPresentation.SQUARE ? 0 : 100}px;
  width: 100%;
  padding: 2px 30px 0 ${(props) => (props.$withPreIcon ? 50 : 14)}px;
  outline: none;
  &:focus {
    border-color: #089fdf;
  }

  &:disabled {
    background: rgba(180, 190, 214, 0.1);
    color: rgba(5, 36, 117, 0.3);
    border-color: rgba(180, 190, 214, 0.1);
  }
  -webkit-appearance: none;
`;

const StyledInput = styled.input`
  ${baseStyles};
  height: ${(props) => (props.$inputSize === TextInputSize.LARGE ? 61 : 40)}px;
  padding: 0 ${(props) => (props.$withPostIcon ? 36 : 14)}px 0
    ${(props) => (props.$withPreIcon ? 50 : 14)}px;
`;

const StyledTextArea = styled.textarea`
  ${baseStyles};
  padding: 4px 30px 0 14px;
`;

const LabelOnBorder = styled.label`
  position: absolute;
  top: -11px;
  left: 32px;
  margin: 0;
  color: ${(props) => props.theme.secondary};
  background: ${(props) => props.theme.white};
  opacity: 0;
  transition: ease-in 200ms;
`;

const LabelOnTopOfInput = styled.label`
  margin: 0 0 6px 0;
  color: ${(props) => props.theme.dark};
  line-height: 110%;
`;

const StyledInputWrapper = styled.div`
  position: relative;

  ${StyledInput}:not(:placeholder-shown) + ${LabelOnBorder} {
    opacity: 1;
  }
`;

const PreIcon = styled.span`
  position: absolute;
  left: ${(props) => (props.$inputSize === TextInputSize.LARGE ? 26 : 18)}px;
  top: ${(props) => (props.$inputSize === TextInputSize.LARGE ? 18 : 10)}px;

  & > svg {
    width: 20px;
  }
`;

const PostIcon = styled.span`
  position: absolute;
  right: ${(props) => (props.$inputSize === TextInputSize.LARGE ? 26 : 18)}px;
  top: ${(props) => (props.$inputSize === TextInputSize.LARGE ? 18 : 10)}px;

  & > svg {
    width: 20px;
  }
`;

export default function TextInput({
  label,
  placeholder,
  value,
  onChange,
  preIcon,
  postIcon,
  id,
  name,
  onBlur,
  onFocus,
  onClick,
  onKeyDown,
  hasError,
  type,
  labelPosition = LabelPosition.ON_TOP_OF_INPUT,
  presentation = TextInputPresentation.SQUARE,
  inputSize = TextInputSize.MEDIUM,
  asTextArea,
  rows,
  disabled,
  className,
  autoComplete,
  ...rest
}) {
  const MainComponent = asTextArea ? StyledTextArea : StyledInput;
  return (
    <>
      {label && labelPosition === LabelPosition.ON_TOP_OF_INPUT && (
        <LabelOnTopOfInput htmlFor={id}>{label}</LabelOnTopOfInput>
      )}
      <StyledInputWrapper>
        {preIcon && <PreIcon $inputSize={inputSize}>{preIcon}</PreIcon>}
        <MainComponent
          className={className}
          data-testid={rest['data-testid']}
          placeholder={placeholder}
          value={value}
          autoComplete={autoComplete}
          onChange={onChange}
          id={id}
          name={name}
          onKeyDown={onKeyDown}
          onBlur={onBlur}
          onFocus={onFocus}
          onClick={onClick}
          $hasError={hasError}
          type={type}
          $presentation={presentation}
          $inputSize={inputSize}
          $withPreIcon={!!preIcon}
          $withPostIcon={!!postIcon}
          rows={rows}
          disabled={disabled}
        />
        {postIcon && <PostIcon $inputSize={inputSize}>{postIcon}</PostIcon>}

        {label && labelPosition === LabelPosition.ON_INPUT_BORDER && (
          <LabelOnBorder htmlFor={id}>{label}</LabelOnBorder>
        )}
      </StyledInputWrapper>
    </>
  );
}
