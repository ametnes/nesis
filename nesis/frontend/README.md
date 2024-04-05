# Nesis

Project Structure

```
|
|- deployment        # CI deployment scripts
|- server            # ExpressJS API service
|- client            # Frontend Client
```

# Setup

## Install node packages

`npm install`

## Run application

### Start the server

```
npm run start:server:local
```

### Start the application

```
cd client
npm start
```

Point your browser to http://localhost:3001/

`Connecting to the TEST API`

```
PROFILE=TEST API_URL=https://test.cloud.ametnes.com/api/optimai npm start
```

`You can ignore SSL certs with`

```
NODE_TLS_REJECT_UNAUTHORIZED=0 PROFILE=TEST API_URL=https://test.cloud.ametnes.com/api/optimai npm start
```

## Run application locally

### Start the backend API server

1. `cd server`
2. `NODE_TLS_REJECT_UNAUTHORIZED=0 PROFILE=TEST API_URL=https://test.cloud.ametnes.com/api/optimai npm start`

### In a separate terminal start the frontend application

1. `cd client`
2. `npm start`

Point your browser to http://localhost:3001/

## Building

```
docker build --build-arg PROFILE=PROD --build-arg PUBLIC_URL=/ -t ametnes/optimai:`cat version.txt` .
```
