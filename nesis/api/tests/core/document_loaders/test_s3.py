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
from nesis.api.core.document_loaders.stores import SqlDocumentStore
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
    """
    Test ingestion of documents from an s3 bucket
    """

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

    ingestor = s3.Processor(
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )
    ingestor.run(
        metadata={"datasource": "documents"},
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
    """
    Test updating documents if they have been updated at the s3 bucket end.
    """

    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "http://localhost:4566",
            "region": "us-east-1",
            "dataobjects": "some-bucket",
        },
    }

    datasource = Datasource(
        name=data["name"],
        connection=data["connection"],
        source_type=DatasourceType.SHAREPOINT,
        status=DatasourceStatus.ONLINE,
    )

    session.add(datasource)
    session.commit()

    self_link = "http://localhost:4566/some-bucket/invalid.pdf"

    # The document record
    document = Document(
        base_uri="http://localhost:4566",
        document_id=str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"{datasource.uuid}:{self_link}",
            )
        ),
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={
            "bucket_name": "some-bucket",
            "object_name": "invalid.pdf",
            "last_modified": "2023-07-18 06:40:07",
        },
        last_modified=strptime("2023-07-19 06:40:07"),
        datasource_id=datasource.uuid,
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
                    "Key": "invalid.pdf",
                    "LastModified": strptime("2023-07-20 06:40:07"),
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

    ingestor = s3.Processor(
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )

    ingestor.run(
        metadata={"datasource": "documents"},
    )

    # The document would be deleted from the rag engine
    _, deletes_kwargs = http_client.deletes.call_args_list[0]
    url = deletes_kwargs["urls"]

    assert url == [
        f"http://localhost:8080/v1/ingest/documents/{document.rag_metadata['data'][0]['doc_id']}"
    ]

    # And then re-ingested
    _, upload_kwargs = http_client.upload.call_args_list[0]
    url = upload_kwargs["url"]
    file_path = upload_kwargs["filepath"]
    metadata = upload_kwargs["metadata"]
    field = upload_kwargs["field"]

    assert url == f"http://localhost:8080/v1/ingest/files"
    assert file_path.endswith("invalid.pdf")
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "some-bucket/invalid.pdf",
            "self_link": self_link,
        },
    )

    # The document has now been updated
    documents = session.query(Document).all()
    assert len(documents) == 1
    assert documents[0].store_metadata["last_modified"] == "2023-07-20 06:40:07"
    assert str(documents[0].last_modified) == "2023-07-20 06:40:07"


@mock.patch("nesis.api.core.document_loaders.s3.boto3.client")
def test_unsync_s3_documents(
    client: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    """
    Test deleting of s3 documents from the rag engine if they have been deleted from the s3 bucket
    """
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "http://localhost:4566",
            "region": "us-east-1",
            "dataobjects": "some-non-existing-bucket",
        },
    }

    datasource = Datasource(
        name=data["name"],
        connection=data["connection"],
        source_type=DatasourceType.SHAREPOINT,
        status=DatasourceStatus.ONLINE,
    )

    session.add(datasource)
    session.commit()

    document = Document(
        base_uri="http://localhost:4566",
        datasource_id=datasource.uuid,
        document_id=str(uuid.uuid4()),
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={"bucket_name": "some-bucket", "object_name": "file/path.pdf"},
        last_modified=datetime.datetime.utcnow(),
    )

    session.add(document)
    session.commit()

    http_client = mock.MagicMock()
    s3_client = mock.MagicMock()

    client.return_value = s3_client
    s3_client.head_object.side_effect = Exception("HeadObject Not Found")

    documents = session.query(Document).all()
    assert len(documents) == 1

    ingestor = s3.Processor(
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )

    ingestor.run(
        metadata={"datasource": "documents"},
    )

    _, upload_kwargs = http_client.deletes.call_args_list[0]
    urls = upload_kwargs["urls"]

    assert (
        urls[0]
        == f"http://localhost:8080/v1/ingest/documents/{document.rag_metadata['data'][0]['doc_id']}"
    )
    documents = session.query(Document).all()
    assert len(documents) == 0


@mock.patch("nesis.api.core.document_loaders.s3.boto3.client")
def test_extract_documents(
    client: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    destination_sql_url = tests.config["database"]["url"]
    # destination_sql_url = "mssql+pymssql://sa:Pa55woR.d12345@localhost:11433/master"
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "https://s3.endpoint",
            "access_key": "",
            "secret_key": "",
            "dataobjects": "buckets",
            "mode": "extract",
            "destination": {
                "sql": {"url": destination_sql_url},
            },
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

    ingestor = s3.Processor(
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )

    extract_store = SqlDocumentStore(
        url=data["connection"]["destination"]["sql"]["url"]
    )

    with Session(extract_store._engine) as session:
        initial_count = len(
            session.query(ingestor._extract_runner._extraction_store.Store)
            .filter()
            .all()
        )

    ingestor.run(
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
            "file_name": "buckets/image.jpg",
            "self_link": "https://s3.endpoint/buckets/image.jpg",
        },
    )

    with Session(extract_store._engine) as session:
        all_documents = (
            session.query(ingestor._extract_runner._extraction_store.Store)
            .filter()
            .all()
        )
        assert len(all_documents) == initial_count + 1


@mock.patch("nesis.api.core.document_loaders.s3.boto3.client")
def test_unextract_documents(
    client: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    """
    Test deleting of s3 documents from the rag engine if they have been deleted from the s3 bucket
    """
    destination_sql_url = tests.config["database"]["url"]
    data = {
        "name": "s3 documents",
        "engine": "s3",
        "connection": {
            "endpoint": "https://s3.endpoint",
            "access_key": "",
            "secret_key": "",
            "dataobjects": "buckets",
            "mode": "extract",
            "destination": {
                "sql": {"url": destination_sql_url},
            },
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
    s3_client = mock.MagicMock()

    client.return_value = s3_client
    s3_client.head_object.side_effect = Exception("HeadObject Not Found")

    minio_ingestor = s3.Processor(
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )

    extract_store = SqlDocumentStore(
        url=data["connection"]["destination"]["sql"]["url"]
    )

    with Session(extract_store._engine) as session:
        session.query(minio_ingestor._extract_runner._extraction_store.Store).delete()
        document = minio_ingestor._extract_runner._extraction_store.Store()
        document.base_uri = data["connection"]["endpoint"]
        document.uuid = str(uuid.uuid4())
        document.filename = "invalid.pdf"
        document.extract_metadata = {"data": [{"doc_id": str(uuid.uuid4())}]}
        document.store_metadata = {
            "bucket_name": "some-bucket",
            "object_name": "file/path.pdf",
        }
        document.last_modified = datetime.datetime.utcnow()

        session.add(document)
        session.commit()

        initial_count = len(
            session.query(minio_ingestor._extract_runner._extraction_store.Store)
            .filter()
            .all()
        )

    minio_ingestor.run(
        metadata={"datasource": "documents"},
    )

    with Session(extract_store._engine) as session:
        documents = session.query(
            minio_ingestor._extract_runner._extraction_store.Store
        ).all()
        assert len(documents) == initial_count - 1
