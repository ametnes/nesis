FROM python:3.11-buster as build

COPY nesis/api/requirements.txt /app/nesis/api/requirements.txt
WORKDIR /app
RUN apt-get update \
    && python -m venv .venv \
    && . .venv/bin/activate \
    && pip install -r /app/nesis/api/requirements.txt \
    && pip install flask==3.0.0

ARG UNAME=nesis
FROM python:3.11.6-slim-bookworm
RUN apt-get update \
    && apt-get clean \
    && adduser --system --home /app --shell /bin/bash nesis

COPY --chown=$UNAME --from=build /app/.venv /app/.venv
COPY --chown=$UNAME nesis/api /app/nesis/api
COPY --chown=$UNAME nesis/__init__.py /app/nesis/__init__.py
COPY --chown=$UNAME nesis/api/start.sh nesis/api/start.sh

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

ARG PORT="8080"
EXPOSE ${PORT}

ENV PYTHONPATH="/app:${PYTHONPATH}"
USER nesis

CMD /bin/bash /app/nesis/api/start.sh

# Remember to set LLAMA_INDEX_CACHE_DIR