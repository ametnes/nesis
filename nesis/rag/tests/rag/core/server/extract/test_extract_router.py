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
        "invoice.pdf",
        # "3-publications.pdf",
    ],
)
def test_extract(injector, client, file_name):
    """
    Tests the extract happy path
    """
    file_path: pathlib.Path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources" / file_name
    )

    with open(file_path.absolute(), "rb") as f:
        response = client.post(
            "/v1/extractions/text",
            files={"file": (file_path.name, f)},
        )
    assert response.status_code == HTTPStatus.OK, response.text
    result = response.json()
    table_results = [
        data["metadata"].get("text_as_html")
        for data in result["data"]
        if data["metadata"].get("text_as_html") is not None
    ]
    assert len(table_results) > 0
    print(table_results[0])
