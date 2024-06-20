import React from 'react';
import styled from 'styled-components';
import { ErrorMessage, Field } from 'formik';
import TextInput from '../inputs/TextInput';
import ReactSelectStyled from '../inputs/Select';
import UncontrolledCheckbox from '../inputs/Checkbox';

function enhanceWithFormikControls(
  Component,
  defaultValue,
  { passErrorState },
) {
  ComponentWithFormik.propTypes = {
    ...Field.propTypes,
    ...Component.propTypes,
  };

  function ComponentWithFormik({ field, form, ...props }) {
    const additionalProps = {};
    if (passErrorState) {
      additionalProps.hasError = Boolean(
        form.errors && form.errors[field.name] && form.touched[field.name],
      );
    }
    return (
      <Component
        name={field.name}
        value={field.value != null ? field.value : defaultValue}
        onChange={(...args) => {
          field.onChange(...args);
        }}
        onBlur={field.onBlur}
        {...props}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            form.handleSubmit();
          }
        }}
        {...additionalProps}
      />
    );
  }

  return ComponentWithFormik;
}

function FormikWorkaroundSelect(props) {
  return (
    <>
      <Field component={ReactSelectWrapper} {...props} />
      <StyledErrorMessage name={props.name} component="div" />
    </>
  );
}

function ReactSelectWrapper(props) {
  const { field, options, form } = props;
  return (
    <ReactSelectStyled
      {...props}
      value={options.find((option) => option.value === field.value)}
      onChange={(option) => {
        form.setFieldValue(field.name, option.value);
      }}
    />
  );
}

const StyledErrorMessage = styled(ErrorMessage)`
  color: ${(props) => props.theme.danger};
  margin-top: 4px;
`;

function enhanceWithFormikField(Component, defaultValue, options = {}) {
  ComponentWithFormik.propTypes = {
    ...Field.propTypes,
    ...Component.propTypes,
  };
  const WithFormikControls = enhanceWithFormikControls(
    Component,
    defaultValue,
    options,
  );

  function ComponentWithFormik(props) {
    const { name } = props;
    return (
      <>
        <Field component={WithFormikControls} {...props} />
        <StyledErrorMessage name={name} component="div" />
      </>
    );
  }

  return ComponentWithFormik;
}

export const TextField = enhanceWithFormikField(TextInput, '', {
  passErrorState: true,
});

export const Checkbox = enhanceWithFormikField(UncontrolledCheckbox, '', {
  passErrorState: true,
});

export const Select = FormikWorkaroundSelect;
