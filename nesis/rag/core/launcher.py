"""FastAPI app creation, logger configuration and main API routes."""

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from injector import Injector

from nesis.rag.core.server.chat.chat_router import chat_router
from nesis.rag.core.server.chunks.chunks_router import chunks_router
from nesis.rag.core.server.completions.completions_router import completions_router
from nesis.rag.core.server.health.health_router import health_router
from nesis.rag.core.server.ingest.ingest_router import ingest_router
from nesis.rag.core.settings.settings import Settings

logger = logging.getLogger(__name__)


def create_app(root_injector: Injector, settings: Settings = None) -> FastAPI:

    # Start the API
    async def bind_injector_to_request(request: Request) -> None:
        request.state.injector = root_injector

    app = FastAPI(dependencies=[Depends(bind_injector_to_request)])

    app.include_router(completions_router)
    app.include_router(chat_router)
    app.include_router(chunks_router)
    app.include_router(ingest_router)
    app.include_router(health_router)

    if settings.server.cors.enabled:
        logger.debug("Setting up CORS middleware")
        app.add_middleware(
            CORSMiddleware,
            allow_credentials=settings.server.cors.allow_credentials,
            allow_origins=settings.server.cors.allow_origins,
            allow_origin_regex=settings.server.cors.allow_origin_regex,
            allow_methods=settings.server.cors.allow_methods,
            allow_headers=settings.server.cors.allow_headers,
        )

    return app
