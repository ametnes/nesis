export default function parseApiErrorMessage(
  err,
  defaultMessage = 'Unknown error',
) {
  if (!err.response) {
    console.error(err);
    return defaultMessage;
  }
  let body = err.response.body;

  if (body && body.message) {
    return body.message;
  } else {
    return defaultMessage;
  }
}
