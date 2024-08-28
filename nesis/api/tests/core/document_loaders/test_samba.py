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


@mock.patch("nesis.api.core.document_loaders.samba.scandir")
@mock.patch("nesis.api.core.document_loaders.samba.stat")
@mock.patch("nesis.api.core.document_loaders.samba.shutil")
def test_ingest(shutil, stat, scandir, cache: mock.MagicMock, session: Session) -> None:
    data = {
        "name": "s3 documents",
        "engine": "samba",
        "connection": {
            "endpoint": r"\\Share",
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

    ingestor = samba.Processor(
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


@mock.patch("nesis.api.core.document_loaders.samba.scandir")
@mock.patch("nesis.api.core.document_loaders.samba.stat")
@mock.patch("nesis.api.core.document_loaders.samba.shutil")
def test_uningest(
    shutil, stat, scandir, cache: mock.MagicMock, session: Session
) -> None:
    """
    Test deleting of s3 documents from the rag engine if they have been deleted from the s3 bucket
    """
    data = {
        "name": "s3 documents",
        "engine": "windows_share",
        "connection": {
            "endpoint": r"\\Share",
            "user": "user",
            "port": "445",
            "password": "password",
            "dataobjects": "buckets",
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
        base_uri=datasource.connection["endpoint"],
        datasource_id=datasource.uuid,
        document_id=str(uuid.uuid4()),
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={
            "bucket_name": "some-bucket",
            "object_name": "file/path.pdf",
            "file_path": r"\\Share\file\path.pdf",
        },
        last_modified=datetime.datetime.utcnow(),
    )

    session.add(document)
    session.commit()

    http_client = mock.MagicMock()

    stat.side_effect = Exception("No such file")

    documents = session.query(Document).all()
    assert len(documents) == 1

    ingestor = samba.Processor(
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


@mock.patch("nesis.api.core.document_loaders.samba.scandir")
@mock.patch("nesis.api.core.document_loaders.samba.stat")
@mock.patch("nesis.api.core.document_loaders.samba.shutil")
def test_update(shutil, stat, scandir, cache: mock.MagicMock, session: Session) -> None:
    """
    Test updating documents if they have been updated at the s3 bucket end.
    """

    data = {
        "name": "s3 documents",
        "engine": "windows_share",
        "connection": {
            "endpoint": r"\\Share",
            "user": "user",
            "port": "445",
            "password": "password",
            "dataobjects": "buckets",
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
        base_uri=r"\\Share",
        document_id=str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                rf"{datasource.uuid}:\\Share\file\path.pdf",
            )
        ),
        filename="invalid.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={
            "bucket_name": "some-bucket",
            "object_name": "invalid.pdf",
            "last_modified": "2023-07-18 06:40:07",
            "file_path": r"\\Share\file\path.pdf",
        },
        last_modified=strptime("2023-07-19 06:40:07"),
        datasource_id=datasource.uuid,
    )

    session.add(document)
    session.commit()

    share = mock.MagicMock()
    share.is_dir.return_value = False
    type(share).name = mock.PropertyMock(return_value="SomeName")
    type(share).path = mock.PropertyMock(return_value=r"\\Share\file\path.pdf")
    scandir.return_value = [share]

    file_stat = mock.MagicMock()
    stat.return_value = file_stat
    type(file_stat).st_size = mock.PropertyMock(return_value=1)
    type(file_stat).st_chgtime = mock.PropertyMock(
        return_value=strptime("2023-07-20 06:40:07").timestamp()
    )

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})

    ingestor = samba.Processor(
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

    # The document has now been updated
    documents = session.query(Document).all()
    assert len(documents) == 1
    assert documents[0].store_metadata["last_modified"] == "2023-07-20 06:40:07"
    assert str(documents[0].last_modified) == "2023-07-20 06:40:07"
