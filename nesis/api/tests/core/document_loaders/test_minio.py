import datetime
import json
import os
import unittest as ut
import unittest.mock as mock
import uuid

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.document_loaders.minio as minio
import nesis.api.core.services as services
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
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )

    # No document records exist
    document_records = session.query(Document).all()
    assert 0 == len(document_records)

    minio_ingestor.run(
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
        source_type=DatasourceType.MINIO,
        status=DatasourceStatus.ONLINE,
    )

    session.add(datasource)
    session.commit()

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({"data": {}})
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
            session.query(minio_ingestor._extract_runner._extraction_store.Store)
            .filter()
            .all()
        )

    minio_ingestor.run(
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

    with Session(extract_store._engine) as session:
        all_documents = (
            session.query(minio_ingestor._extract_runner._extraction_store.Store)
            .filter()
            .all()
        )
        assert len(all_documents) == initial_count + 1


@mock.patch("nesis.api.core.document_loaders.minio.Minio")
def test_uningest_documents(
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
            # "user": "test",
            # "password": "test",
            "region": "us-east-1",
            "dataobjects": "some-non-existing-bucket",
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

    document = Document(
        base_uri="http://localhost:4566",
        document_id=str(uuid.uuid4()),
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={"bucket_name": "some-bucket", "object_name": "file/path.pdf"},
        last_modified=datetime.datetime.utcnow(),
    )

    session.add(document)
    session.commit()

    http_client = mock.MagicMock()
    minio_client = mock.MagicMock()

    client.return_value = minio_client
    minio_client.stat_object.side_effect = Exception("NoSuchKey - does not exist")

    documents = session.query(Document).all()
    assert len(documents) == 1

    minio_ingestor = minio.MinioProcessor(
        config=tests.config,
        http_client=http_client,
        cache_client=cache,
        datasource=datasource,
    )

    # # No document records exist
    # document_records = session.query(Document).all()
    # assert 0 == len(document_records)

    minio_ingestor.run(
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


@mock.patch("nesis.api.core.document_loaders.minio.Minio")
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
    minio_client = mock.MagicMock()

    client.return_value = minio_client
    minio_client.stat_object.side_effect = Exception("NoSuchKey - does not exist")

    minio_ingestor = minio.MinioProcessor(
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
