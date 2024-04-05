FROM node:20 as builder

ARG PROFILE
ARG PUBLIC_URL=/nesis/
ENV APP_HOME=/app
ENV PUBLIC_URL ${PUBLIC_URL}
ENV PROFILE ${PROFILE}

# Create app directory
WORKDIR /app
COPY nesis/frontend .

# Install app dependencies and bundle app source
RUN ls -al /app && npm install --only=production
# The client
RUN cd /app/client && npm install --only=production && /bin/bash /app/build.sh $PROFILE
RUN mkdir -p /app/dist/client \
    && cp -rf /app/client/build/* /app/dist/client/ \
    && cp -rf /app/server /app/dist/ \
    && cp -rf /app/node_modules /app/dist \
    && cp /app/package.json /app/dist/ \
    && mkdir /app/dist/logs
RUN find /app/dist/client -name node_modules -o -name src -exec rm -rf {} \; || true

FROM node:20
ARG PROFILE
ENV PUBLIC_URL ${PUBLIC_URL}
ENV APP_HOME=/app/nesis/client
ENV PROFILE ${PROFILE}
ENV UNAME=nesis

# Create app directory
WORKDIR /app/nesis
RUN adduser --system --home /app/nesis --shell /bin/bash nesis

COPY --from=builder --chown=nesis /app/dist .
EXPOSE 8000

USER $UNAME
CMD PROFILE=$PROFILE npm run start:server
