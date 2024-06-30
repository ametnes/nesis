import pathlib
from typing import Any, Dict

import pytest
from injector import Injector

from nesis.rag.core.server.extract.extract_service import ExtractService
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

    return settings(overrides={"llm": {"mode": "mock"}})


def test_extract_text(injector):
    """
    Test to ensure we can ingest all files. This test helps make sure we have all the necessary libraries installed.
    This test DOES NOT test for accuracy of the extracted data.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute()
        / "resources"
        / "3-publications.pdf"
    )

    extract_service: ExtractService = injector.get(ExtractService)

    extracted_list: list[Dict[str, Any]] = extract_service.extract_file(
        file_name=file_path.name,
        file_data=file_path,
        metadata={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    assert len(extracted_list) > 0


def test_extract_table(injector):
    """
    Test to ensure we can ingest all files. This test helps make sure we have all the necessary libraries installed.
    This test DOES NOT test for accuracy of the extracted data.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources/invoice.pdf"
    )

    extract_service: ExtractService = injector.get(ExtractService)

    extracted_list: list[Dict[str, Any]] = extract_service.extract_file(
        file_name=file_path.name,
        file_data=file_path,
        metadata={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    assert len(extracted_list) > 0
