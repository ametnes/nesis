import json
import pathlib
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from injector import Injector

from nesis.rag.core.settings.settings import Settings
from nesis.rag import tests


@pytest.fixture
def injector(settings) -> Injector:
    from nesis.rag.core.di import create_application_injector

    return create_application_injector(settings=settings)


@pytest.fixture
def client(injector, settings) -> TestClient:
    from nesis.rag.core.launcher import create_app

    app = create_app(root_injector=injector, settings=settings)
    return TestClient(app=app)


@pytest.fixture
def settings() -> Settings:
    from nesis.rag.core.settings.settings import settings

    return settings(overrides={"llm": {"mode": "mock"}})


@pytest.mark.parametrize(
    "file_name",
    [
        # "test2_transcript.txt",
        "file-sample_150kB.pdf",
    ],
)
def test_ingest_supported(injector, client, file_name):
    """
    Tests the ingestion happy path
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources" / file_name
    )

    metadata = {"datasource": "documents"}

    with open(file_path.absolute(), "rb") as f:
        response = client.post(
            "/v1/ingest/files",
            files={"file": (file_path.name, f)},
            params={"metadata": json.dumps(metadata)},
            data={"metadata": json.dumps(metadata)},
        )
    # print(response.text)
    assert response.status_code == HTTPStatus.OK, response.text
    result = response.json()
    assert len(result["data"]) > 0
    for item in result["data"]:
        assert item["doc_metadata"]["datasource"] == "documents"


def test_ingest_invalid_metadata(injector, client):
    """
    Tests invalid metadata
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute()
        / "resources/file-sample_150kB.pdf"
    )

    with open(file_path.absolute(), "rb") as f:
        response = client.post(
            "/v1/ingest/files",
            files={"file": (file_path.name, f)},
            params={"metadata": "s"},
            data={"metadata": "d"},
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_ingest_unsupported(injector, client):
    """
    If we have any failures, we should return a 400 to indicate the file format isn't supported
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute()
        / "resources/file-sample_100kB.doc"
    )

    metadata = {"datasource": "documents"}

    with open(file_path.absolute(), "rb") as f:
        response = client.post(
            "/v1/ingest/files",
            files={"file": (file_path.name, f)},
            params={"metadata": json.dumps(metadata)},
            data={"metadata": json.dumps(metadata)},
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json().get("detail") is not None


def test_list_ingested(injector, client):
    response = client.get("/v1/ingest/files")
    assert response.status_code == HTTPStatus.OK
