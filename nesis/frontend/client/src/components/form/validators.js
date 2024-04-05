export function required(value) {
  let error;
  if (!value) {
    error = 'Required';
  }
  return error;
}

export function lessOrEqual(maxValue) {
  return function requireMax(value) {
    let error;
    if (value != null && value > maxValue) {
      error = 'Must be less or equal to ' + maxValue;
    }
    return error;
  };
}

export function moreThan(minValue) {
  return function requireMoreThan(value) {
    let error;
    if (value != null && value < minValue) {
      error = 'Must be more than ' + minValue;
    }
    return error;
  };
}

export function matchesRegex(regex, message = 'Input is invalid') {
  return function validate(value) {
    let error;
    if (!regex.test(String(value).toLowerCase())) {
      error = message;
    }
    return error;
  };
}

export function isOneOf(allowedValues) {
  return function validateValue(value) {
    if (value && !allowedValues.includes(value)) {
      return 'Selected value is not part of allowed values';
    }
    return undefined;
  };
}

export function composeValidators(...validators) {
  return (value) => {
    let error;
    validators.some((validator) => {
      error = validator(value);
      return !!error;
    });
    return error;
  };
}
