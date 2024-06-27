import pathlib
import uuid
from typing import List

import pytest
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader

from nesis.rag import tests
from nesis.rag.core.components.ingest.ingest_helper import IngestionHelper
from nesis.rag.core.components.ingest.readers import TiffReader, PdfReader


@pytest.mark.parametrize(
    "file_name, expected",
    [
        ("file-sample_150kB.pdf", ["Lorem", "ipsum"]),
        ("file-sample_500kB.docx", ["Lorem", "ipsum"]),
        ("rfc791.txt", ["INTERNET", "PROTOCOL"]),
        ("website-traffic-dashboard.csv", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.ods", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.xlsx", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.pdf", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.jpg", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.png", ["web", "traffic", "dashboard"]),
        ("website-traffic-dashboard.tiff", ["web", "traffic", "dashboard"]),
        ("introduction-to-nesis.mp3", ["canada", "england"]),
        ("introduction-to-nesis.mp4", ["canada", "england"]),
        ("brochure.epub", ["product", "brochure"]),
    ],
)
def test_ingestion(file_name: str, expected: List[str]):
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


def test_ingestion_metadata_inclusion():
    """
    Test to ensure the metadata we want to exclude is indeed excluded.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute()
        / "resources"
        / "website-traffic-dashboard.tiff"
    )

    # Exclude some random item that would never exist anyway
    reader: BaseReader = TiffReader(
        config={"metadata_exclusion_list": [str(uuid.uuid4())]}
    )

    document_list: list[Document] = reader.load_data(
        file=file_path,
        extra_info={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    assert len(document_list) > 0
    assert len([doc for doc in document_list if "languages" in doc.metadata.keys()]) > 0


def test_ingestion_metadata_exclusion():
    """
    Test to ensure the metadata we want to exclude is indeed excluded.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute()
        / "resources"
        / "website-traffic-dashboard.tiff"
    )

    reader: BaseReader = TiffReader(config={"metadata_exclusion_list": ["languages"]})

    document_list: list[Document] = reader.load_data(
        file=file_path,
        extra_info={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    assert len(document_list) > 0
    assert (
        len([doc for doc in document_list if "languages" in doc.metadata.keys()]) == 0
    )


def test_ingestion_default_metadata_exclusion():
    """
    Test to ensure the metadata we want to exclude is indeed excluded.
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute()
        / "resources"
        / "website-traffic-dashboard.tiff"
    )

    reader: BaseReader = TiffReader()

    document_list: list[Document] = reader.load_data(
        file=file_path,
        extra_info={
            "file_name": str(file_path.absolute()),
            "datasource": "rfc-documents",
        },
    )

    assert len(document_list) > 0
    assert (
        len([doc for doc in document_list if "file_directory" in doc.metadata.keys()])
        == 0
    )
