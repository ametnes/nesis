import pathlib
import uuid

import pytest
from fastapi.testclient import TestClient
from injector import Injector

from nesis.rag.core.server.ingest.ingest_service import IngestService
from nesis.rag.core.settings.settings import Settings
from nesis.rag import tests
from nesis.rag.core.open_ai.openai_models import OpenAICompletion
from nesis.rag.core.server.completions.completions_service import CompletionsService


@pytest.fixture(autouse=True)
def injector(settings) -> Injector:
    from nesis.rag.core.di import create_application_injector

    return create_application_injector(settings=settings)


@pytest.fixture(
    autouse=True,
    scope="module",
    params=[
        {"vectorstore": {"database": "pgvector"}},
        {"vectorstore": {"database": "chroma"}},
        {"vectorstore": {"database": "qdrant"}},
    ],
)
def settings(request) -> Settings:
    from nesis.rag.core.settings.settings import settings

    overrides = {"llm": {"mode": "mock"}, **request.param}
    return settings(overrides=overrides)


def test_vector_storage(injector):
    from nesis.rag.core.open_ai.extensions.context_filter import ContextFilter
    from nesis.rag.core.server.completions.completions_service import (
        CompletionsBody,
    )

    ingest_service = injector.get(IngestService)
    completions_service = injector.get(CompletionsService)

    print(settings)
    file_path = pathlib.Path(tests.__file__).parent.absolute() / "resources/rfc791.txt"
    ingest_service.ingest_file(
        file_name=file_path.name,
        file_data=file_path,
        metadata={
            "file_name": "rfc/rfc791.txt",
            "datasource": "rfc-documents",
        },
    )
    #

    # With correct filters, we get sources back
    context_filter = ContextFilter(filters={"datasource": ["rfc-documents"]})
    body = CompletionsBody(
        prompt="Summarise the internet protocol specification",
        context_filter=context_filter,
        use_context=True,
    )
    completion: OpenAICompletion = completions_service.completion(body=body)
    assert len(completion.choices[0].sources) > 0

    # print(completion.model_dump_json())

    # With incorrect filters, we get no sources back
    context_filter = ContextFilter(filters={"datasource": [str(uuid.uuid4())]})
    body = CompletionsBody(
        prompt="Summarise the internet protocol specification",
        context_filter=context_filter,
        use_context=True,
    )
    completion: OpenAICompletion = completions_service.completion(body=body)

    # print(completion.model_dump_json())

    assert len(completion.choices[0].sources) == 0
