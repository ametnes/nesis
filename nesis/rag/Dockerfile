FROM python:3.11-buster as build
# Options are cpu and cuda
ARG CORE=cpu
COPY nesis/rag/requirements.txt /app/nesis/rag/requirements.txt
COPY nesis/rag/requirements-huggingface.txt /app/nesis/rag/requirements-huggingface.txt
COPY nesis/rag/requirements-torch-cpu-x86.txt /app/nesis/rag/requirements-torch-cpu-x86.txt

RUN python -m venv /app/.venv
RUN if [ "$CORE" = "cpu" ] ; \
    then /app/.venv/bin/pip install \
    -r /app/nesis/rag/requirements.txt \
    -r /app/nesis/rag/requirements-torch-cpu-x86.txt \
    -r /app/nesis/rag/requirements-huggingface.txt \
    --default-timeout=1200 ; \
    fi
RUN if [ "$CORE" = "cuda" ] ; \
    then /app/.venv/bin/pip install \
    -r /app/nesis/rag/requirements.txt \
    -r /app/nesis/rag/requirements-huggingface.txt \
    --default-timeout=1200 ; \
    fi

RUN /app/.venv/bin/pip install -U transformers

FROM python:3.11.6-slim-bookworm
ARG NESIS_VERSION
ARG UID=1001
ARG GID=1002
ARG UNAME=nesis
RUN apt-get update \
    && apt-get clean \
    && addgroup --system --gid $GID $UNAME \
    && adduser --system --uid $UID --gid $GID --home /app --shell /bin/bash $UNAME \
    && apt install ffmpeg tesseract-ocr poppler-utils -y

WORKDIR /app

COPY --chown=nesis --from=build /app/.venv .venv
COPY --chown=nesis nesis/rag nesis/rag
COPY --chown=nesis nesis/__init__.py nesis/__init__.py

ENV PATH="/app/.venv/bin/:$PATH"
ENV HOME=/app

ARG PORT="8080"
EXPOSE ${PORT}

ENV PYTHONPATH="${PYTHONPATH}:/app/nesis"
ENV NESIS_VERSION=$NESIS_VERSION
USER 1001
CMD python nesis/rag/core/main.py

# Remember to set LLAMA_INDEX_CACHE_DIR
