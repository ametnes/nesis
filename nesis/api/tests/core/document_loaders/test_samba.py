import json
import os
import time
import unittest as ut
import unittest.mock as mock

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.document_loaders.samba as samba
import nesis.api.core.services as services
from nesis.api import tests
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


@mock.patch("nesis.api.core.document_loaders.samba.scandir")
@mock.patch("nesis.api.core.document_loaders.samba.stat")
@mock.patch("nesis.api.core.document_loaders.samba.shutil")
def test_fetch_documents(
    shutil, stat, scandir, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "https://s3.endpoint",
            "user": "user",
            "port": "445",
            "password": "password",
            "dataobjects": "buckets",
        },
    }

    datasource = Datasource(
        name=data["name"],
        connection=data["connection"],
        source_type=DatasourceType.MINIO,
        status=DatasourceStatus.ONLINE,
    )

    session.add(datasource)
    session.commit()

    share = mock.MagicMock()
    share.is_dir.return_value = False
    type(share).name = mock.PropertyMock(return_value="SomeName")
    type(share).path = mock.PropertyMock(return_value=r"\\Share\SomeName")
    scandir.return_value = [share]

    file_stat = mock.MagicMock()
    stat.return_value = file_stat
    type(file_stat).st_size = mock.PropertyMock(return_value=1)
    type(file_stat).st_chgtime = mock.PropertyMock(return_value=time.time())

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})

    samba.fetch_documents(
        connection=data["connection"],
        http_client=http_client,
        metadata={"datasource": "documents"},
        rag_endpoint="http://localhost:8080",
        cache_client=cache,
    )

    _, upload_kwargs = http_client.upload.call_args_list[0]
    url = upload_kwargs["url"]
    file_path = upload_kwargs["filepath"]
    metadata = upload_kwargs["metadata"]
    field = upload_kwargs["field"]

    assert url == f"http://localhost:8080/v1/ingest/files"
    assert file_path.endswith("SomeName")
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": r"\\Share\SomeName",
            "self_link": r"\\Share\SomeName",
        },
    )
