import pathlib

import pytest
from injector import Injector
from llama_index.core.base.llms.types import ChatMessage

from nesis.rag.core.server.chat.chat_service import ChatService, Completion
from nesis.rag.core.server.ingest.ingest_service import IngestService
from nesis.rag.core.settings.settings import Settings
from nesis.rag import tests
from nesis.rag.core.server.ingest.model import IngestedDoc


@pytest.fixture
def injector(settings) -> Injector:
    from nesis.rag.core.di import create_application_injector

    return create_application_injector(settings=settings)


@pytest.fixture
def settings() -> Settings:
    from nesis.rag.core.settings.settings import settings

    return settings(
        overrides={
            "llm": {"mode": "mock", "token_limit": 100000},
            "vectorstore": {"similarity_top_k": "20"},
        }
    )


def test_chat_service_similarity_top_k(injector):
    """
    Test to ensure similarity_top_k setting takes effect.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources" / "rfc791.txt"
    )

    ingest_service = injector.get(IngestService)

    ingested_list: list[IngestedDoc] = ingest_service.ingest_file(
        file_name=file_path.name,
        file_data=file_path,
        metadata={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    chat_service = injector.get(ChatService)
    completion: Completion = chat_service.chat(
        use_context=True,
        messages=[
            ChatMessage.from_str(
                content="describe the internet protocol from the darpa internet program"
            )
        ],
    )

    assert len(completion.sources) == 20
