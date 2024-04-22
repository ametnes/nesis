import datetime
import json
import os
import random
import unittest as ut
import unittest.mock as mock
import uuid
import botocore

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.core.document_loaders.s3 as s3
from nesis.api import tests
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine
from nesis.api.core.models.entities import (
    Datasource,
    DatasourceType,
    DatasourceStatus,
    Document,
)
from nesis.api.core.util import http
from nesis.api.core.util.dateutil import strptime


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


@mock.patch("nesis.api.core.document_loaders.s3.boto3.client")
def test_sync_documents(
    client: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "http://localhost:4566",
            # "user": "test",
            # "password": "test",
            "region": "us-east-1",
            "dataobjects": "my-test-bucket",
        },
    }

    datasource = Datasource(
        name=data["name"],
        connection=data["connection"],
        source_type=DatasourceType.S3,
        status=DatasourceStatus.ONLINE,
    )

    session.add(datasource)
    session.commit()

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})
    s3_client = mock.MagicMock()

    client.return_value = s3_client
    paginator = mock.MagicMock()
    paginator.paginate.return_value = [
        {
            "KeyCount": 1,
            "Contents": [
                {
                    "Key": "image.jpg",
                    "LastModified": strptime("2023-07-18 06:40:07"),
                    "ETag": '"d41d8cd98f00b204e9800998ecf8427e"',
                    "Size": 0,
                    "StorageClass": "STANDARD",
                    "Owner": {
                        "DisplayName": "webfile",
                        "ID": "75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a",
                    },
                }
            ],
        }
    ]
    s3_client.get_paginator.return_value = paginator

    s3.fetch_documents(
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
    assert file_path.endswith("image.jpg")
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "my-test-bucket/image.jpg",
            "self_link": "http://localhost:4566/my-test-bucket/image.jpg",
        },
    )

    assert len(session.query(Document).all()) == 1


@mock.patch("nesis.api.core.document_loaders.s3.boto3.client")
def test_update_sync_documents(
    client: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "http://localhost:4566",
            "region": "us-east-1",
            "dataobjects": "my-test-bucket",
        },
    }

    document = Document(
        base_uri="http://localhost:4566",
        document_id="d41d8cd98f00b204e9800998ecf8427e",
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={
            "bucket_name": "some-bucket",
            "object_name": "file/path.pdf",
            "last_modified": "2023-07-18 06:40:07",
        },
    )

    session.add(document)
    session.commit()

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})
    s3_client = mock.MagicMock()

    client.return_value = s3_client
    paginator = mock.MagicMock()
    paginator.paginate.return_value = [
        {
            "KeyCount": 1,
            "Contents": [
                {
                    "Key": "image.jpg",
                    "LastModified": strptime("2023-07-19 06:40:07"),
                    "ETag": "d41d8cd98f00b204e9800998ecf8427e",
                    "Size": 0,
                    "StorageClass": "STANDARD",
                    "Owner": {
                        "DisplayName": "webfile",
                        "ID": "75aa57f09aa0c8caeab4f8c24e99d10f8e7faeebf76c078efc7c6caea54ba06a",
                    },
                }
            ],
        }
    ]
    s3_client.get_paginator.return_value = paginator

    s3.fetch_documents(
        connection=data["connection"],
        http_client=http_client,
        metadata={"datasource": "documents"},
        rag_endpoint="http://localhost:8080",
        cache_client=cache,
    )

    # The document would be deleted from the rag engine
    _, upload_kwargs = http_client.delete.call_args_list[0]
    url = upload_kwargs["url"]

    assert (
        url
        == f"http://localhost:8080/v1/ingest/documents/{document.rag_metadata['data'][0]['doc_id']}"
    )

    # And then re-ingested
    _, upload_kwargs = http_client.upload.call_args_list[0]
    url = upload_kwargs["url"]
    file_path = upload_kwargs["filepath"]
    metadata = upload_kwargs["metadata"]
    field = upload_kwargs["field"]

    assert url == f"http://localhost:8080/v1/ingest/files"
    assert file_path.endswith("image.jpg")
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "my-test-bucket/image.jpg",
            "self_link": "http://localhost:4566/my-test-bucket/image.jpg",
        },
    )

    # The document has now been updated
    documents = session.query(Document).all()
    assert len(documents) == 1
    assert documents[0].store_metadata["last_modified"] == "2023-07-19 06:40:07"


@mock.patch("nesis.api.core.document_loaders.s3.boto3.client")
def test_unsync_s3_documents(
    client: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "http://localhost:4566",
            # "user": "test",
            # "password": "test",
            "region": "us-east-1",
            "dataobjects": "some-non-existing-bucket",
        },
    }

    document = Document(
        base_uri="http://localhost:4566",
        document_id=str(uuid.uuid4()),
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={"bucket_name": "some-bucket", "object_name": "file/path.pdf"},
    )

    session.add(document)
    session.commit()

    http_client = mock.MagicMock()
    s3_client = mock.MagicMock()

    client.return_value = s3_client
    s3_client.head_object.side_effect = Exception("HeadObject Not Found")

    documents = session.query(Document).all()
    assert len(documents) == 1

    s3.fetch_documents(
        connection=data["connection"],
        http_client=http_client,
        metadata={"datasource": "documents"},
        rag_endpoint="http://localhost:8080",
        cache_client=cache,
    )

    _, upload_kwargs = http_client.delete.call_args_list[0]
    url = upload_kwargs["url"]

    assert (
        url
        == f"http://localhost:8080/v1/ingest/documents/{document.rag_metadata['data'][0]['doc_id']}"
    )
    documents = session.query(Document).all()
    assert len(documents) == 0
