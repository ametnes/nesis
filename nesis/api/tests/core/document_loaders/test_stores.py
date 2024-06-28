import datetime
import json
import os
import time
import unittest as ut
import unittest.mock as mock
import uuid

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.document_loaders.samba as samba
import nesis.api.core.services as services
from nesis.api import tests
from nesis.api.core.document_loaders.stores import SqlDocumentStore
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine
from nesis.api.core.models.entities import (
    Datasource,
    DatasourceType,
    DatasourceStatus,
)


@pytest.fixture
def session() -> None:
    return DBSession()


@pytest.fixture
def cache() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture(autouse=True)
def configure() -> None:
    os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1"

    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)


def test_sql_store(cache: mock.MagicMock, session: Session) -> None:
    config = tests.config.get("database") or {}
    store = SqlDocumentStore(url=config["url"])
    doc_id = str(uuid.uuid4())
    record: SqlDocumentStore.Document = store.save(
        document_id=doc_id,
        datasource_id=doc_id,
        extract_metadata="<table></table>",
        store_metadata={"id": "te"},
        last_modified=str(datetime.datetime.now()),
    )

    assert record.id is not None

    store.delete(document_id=doc_id)
