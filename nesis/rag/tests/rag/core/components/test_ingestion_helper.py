import pathlib

import pytest
from llama_index.core import Document

from nesis.rag import tests
from nesis.rag.core.components.ingest.ingest_helper import IngestionHelper


@pytest.mark.parametrize(
    "file_name, expected",
    [
        ("file-sample_150kB.pdf", ["Lorem", "ipsum"]),
        ("file-sample_500kB.docx", ["Lorem", "ipsum"]),
        ("samplepptx.pptx", None),
        ("rfc791.txt", ["INTERNET", "PROTOCOL"]),
        ("sales_data_sample.json", None),
        ("website-traffic-dashboard.csv", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.ods", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.xlsx", ["web", "traffic", "dashboard"]),
        # ("website-traffic-dashboard.png", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.pdf", ["web", "traffic", "dashboard"]),
        # ("website-traffic-dashboard.jpg", ["web", "traffic", "dashboard"]),
        # ("website-traffic-dashboard.tiff", ["web", "traffic", "dashboard"]),
        ("introduction-to-nesis.mp3", ["canada", "england"]),
        ("introduction-to-nesis.mp4", ["canada", "england"]),
    ],
)
def test_ingestion(file_name: str, expected: list[str]):
    """
    Test to ensure we can ingest all files. This test helps make sure we have all the necessary libraries installed.
    This test also tests for accuracy of the extracted data.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources" / file_name
    )

    document_list: list[Document] = IngestionHelper.transform_file_into_documents(
        file_name=file_path.name,
        file_data=file_path,
        metadata={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    assert len(document_list) > 0
    if expected:
        assert (
            len(
                [
                    doc
                    for doc in document_list
                    for content in expected
                    if content.lower() in doc.text.lower()
                ]
            )
            > 0
        )
