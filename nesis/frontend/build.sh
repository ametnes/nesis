#!/usr/bin/env bash
PROFILE=$1
if [ "${PROFILE}" = "PROD" ]; then
    npm run build:prod
else
    npm run build
fi;
