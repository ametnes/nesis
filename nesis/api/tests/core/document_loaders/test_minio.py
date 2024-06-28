import datetime
import json
import os
import random
import unittest as ut
import unittest.mock as mock
import uuid

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.core.document_loaders.minio as minio
from nesis.api import tests
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine
from nesis.api.core.models.entities import (
    Datasource,
    Document,
)

from nesis.api.core.models.objects import (
    DatasourceType,
    DatasourceStatus,
)
from nesis.api.core.util import http


@pytest.fixture
def session() -> None:
    return DBSession()


@pytest.fixture
def cache() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture(autouse=True)
def configure() -> None:
    os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1"

    # self.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)


@mock.patch("nesis.api.core.document_loaders.minio.Minio")
def test_ingest_documents(
    minio_instance: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "https://s3.endpoint",
            "access_key": "",
            "secret_key": "",
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

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})
    minio_client = mock.MagicMock()
    bucket = mock.MagicMock()

    minio_instance.return_value = minio_client
    type(bucket).etag = mock.PropertyMock(return_value=str(uuid.uuid4()))
    type(bucket).bucket_name = mock.PropertyMock(return_value="SomeName")
    type(bucket).object_name = mock.PropertyMock(return_value="SomeName")
    type(bucket).last_modified = mock.PropertyMock(return_value=datetime.datetime.now())
    type(bucket).size = mock.PropertyMock(return_value=1000)
    type(bucket).version_id = mock.PropertyMock(return_value="2")

    minio_client.list_objects.return_value = [bucket]

    minio_ingestor = minio.MinioProcessor(
        config=tests.config, http_client=http_client, cache_client=cache
    )

    # No document records exist
    document_records = session.query(Document).all()
    assert 0 == len(document_records)

    minio_ingestor.run(
        datasource=datasource,
        metadata={"datasource": "documents"},
    )

    _, upload_kwargs = http_client.upload.call_args_list[0]
    url = upload_kwargs["url"]
    metadata = upload_kwargs["metadata"]
    field = upload_kwargs["field"]

    assert url == f"http://localhost:8080/v1/ingest/files"
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "buckets/SomeName",
            "self_link": "https://s3.endpoint/buckets/SomeName",
        },
    )

    # Expect one document record to exist
    document_records = session.query(Document).all()
    assert 1 == len(document_records)


@mock.patch("nesis.api.core.document_loaders.minio.Minio")
def test_extract_documents(
    minio_instance: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "https://s3.endpoint",
            "access_key": "",
            "secret_key": "",
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

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})
    minio_client = mock.MagicMock()
    bucket = mock.MagicMock()

    minio_instance.return_value = minio_client
    type(bucket).etag = mock.PropertyMock(return_value=str(uuid.uuid4()))
    type(bucket).bucket_name = mock.PropertyMock(return_value="SomeName")
    type(bucket).object_name = mock.PropertyMock(return_value="SomeName")
    type(bucket).last_modified = mock.PropertyMock(return_value=datetime.datetime.now())
    type(bucket).size = mock.PropertyMock(return_value=1000)
    type(bucket).version_id = mock.PropertyMock(return_value="2")

    minio_client.list_objects.return_value = [bucket]

    minio_ingestor = minio.MinioProcessor(
        config=tests.config, http_client=http_client, cache_client=cache, mode="extract"
    )

    minio_ingestor.run(
        datasource=datasource,
        metadata={"datasource": "documents"},
    )

    _, upload_kwargs = http_client.upload.call_args_list[0]
    url = upload_kwargs["url"]
    metadata = upload_kwargs["metadata"]
    field = upload_kwargs["field"]

    assert url == "http://localhost:8080/v1/extractions/text"
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "buckets/SomeName",
            "self_link": "https://s3.endpoint/buckets/SomeName",
        },
    )
