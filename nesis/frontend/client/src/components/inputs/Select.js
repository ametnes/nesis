// import styled from 'styled-components/macro';
import styled from 'styled-components';
import Select from 'react-select';
import React from 'react';

const ReactSelectElement = styled(Select)`
  .react-select__control {
    background: none;
    border: 2px solid #3368f21a;
    border-radius: 10px;
    cursor: pointer;
    padding: 0;
    height: 41px;
    font-weight: 500;
    width: ${(props) => (props.$width ? props.$width + 'px' : '100%')};
  }

  .react-select__control--menu-is-open {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    border-bottom-color: transparent;
    border-width: 2px;
  }

  .react-select__control--is-focused {
    border-color: #3368f21a;
    box-shadow: none;
  }

  .react-select__control--is-focused:hover {
    border-color: #3368f21a;
  }

  .react-select__menu {
    margin: 0;
    border: 2px solid #e4ecff;
    box-sizing: border-box;
    border-radius: 0 0 18px 18px;
    box-shadow: none;
    border-top: none;
  }
`;

const Label = styled.label`
  margin: 0 0 6px 0;
  color: ${(props) => props.theme.dark};
  background: none;
  line-height: 110%;
`;

const ReactSelectStyled = ({ label, className, ...props }) => (
  <>
    {label && <Label>{label}</Label>}
    <ReactSelectElement
      classNamePrefix="react-select"
      className={className}
      {...props}
    />
  </>
);

export default ReactSelectStyled;
