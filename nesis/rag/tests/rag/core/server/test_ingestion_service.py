import pathlib

import pytest
from injector import Injector

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


@pytest.mark.parametrize(
    "file_name",
    [
        "file-sample_150kB.pdf",
        "file-sample_500kB.docx",
        "samplepptx.pptx",
        "rfc791.txt",
        "free-hugs.jpg",
        "free-hugs.jpeg",
        "free-hugs.png",
        "sales_data_sample.json",
        "website-traffic-dashboard.csv",
        "website-traffic-dashboard.ods",
        "website-traffic-dashboard.xlsx",
        "website-traffic-dashboard.png",
        "website-traffic-dashboard.pdf",
        "website-traffic-dashboard.jpg",
        "website-traffic-dashboard.tiff",
        "introduction-to-nesis.mp4",
    ],
)
def test_ingestion_supported(injector, file_name):
    """
    Test to ensure we can ingest all files. This test helps make sure we have all the necessary libraries installed
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources" / file_name
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

    assert len(ingested_list) > 0
