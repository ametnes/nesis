const profile = {
  PROD: {
    SERVICE_ENDPOINT: `${process.env.API_URL}/v1`,
  },
  TEST: {
    SERVICE_ENDPOINT: `${process.env.API_URL}/v1`,
  },
  DEV: {
    SERVICE_ENDPOINT: `http://localhost:6000/v1`,
  },
};

module.exports.profile = profile;
