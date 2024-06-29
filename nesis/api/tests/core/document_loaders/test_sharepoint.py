import json
import os
import datetime
import uuid

import unittest as ut
import unittest.mock as mock

from sqlalchemy.orm.session import Session

import nesis.api.core.document_loaders.sharepoint as sharepoint
from nesis.api import tests
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine
import nesis.api.core.services as services
from nesis.api.core.models.entities import (
    Datasource,
    Document,
)

from nesis.api.core.models.objects import (
    DatasourceType,
    DatasourceStatus,
)


@mock.patch("nesis.api.core.document_loaders.sharepoint.ClientContext")
def test_sync_sharepoint_documents(
    client_context: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "sharepoint documents",
        "engine": "sharepoint",
        "connection": {
            "endpoint": "https://ametnes.sharepoint.com/sites/nesis-test/",
            "client_id": "<sharepoint_app_client_id>",
            "tenant_id": "<sharepoint_app_tenant_id>",
            "thumbprint": "<sharepoint_app_cert_thumbprint>",
            "certificate": "path_to_private_cert_keyfile",
            "dataobjects": "Books",
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

    sp_client_context = mock.MagicMock()
    root_folder = mock.MagicMock()

    file_mock = mock.MagicMock()
    _folders = mock.MagicMock()

    client_context().with_client_certificate.return_value = sp_client_context

    sp_client_context.web.default_document_library.return_value.root_folder = (
        root_folder
    )

    type(file_mock).name = mock.PropertyMock(return_value="some_file.pdf")
    type(file_mock).serverRelativeUrl = mock.PropertyMock(
        return_value=r"/sites/nesit-test/Shared Documents/some_file.pdf"
    )
    type(file_mock).unique_id = mock.PropertyMock(return_value="123123-123131-1313")
    type(file_mock).time_last_modified = mock.PropertyMock(return_value=datetime.time())
    type(file_mock).length = mock.PropertyMock(return_value=1023)
    type(file_mock).author = mock.PropertyMock(return_value="file author")

    root_folder.folders.get_by_path.return_value = _folders
    _folders.get_files.return_value.execute_query.return_value = [file_mock]

    file_download = mock.MagicMock()
    file_mock.download.return_value.execute_query.return_value = file_download

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})

    sharepoint.fetch_documents(
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
    assert file_path.endswith("some_file.pdf")
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "some_file.pdf",
            "self_link": r"https://ametnes.sharepoint.com/sites/nesit-test/Shared Documents/some_file.pdf",
        },
    )


@mock.patch("nesis.api.core.document_loaders.sharepoint.ClientContext")
def test_sync_updated_sharepoint_documents(
    sharepoint_context: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    """
    Test updating documents if they have been updated on Sharepoint
    """

    data = {
        "name": "sharepoint documents",
        "engine": "sharepoint",
        "connection": {
            "endpoint": "https://ametnes.sharepoint.com/sites/nesis-test/",
            "client_id": "<sharepoint_app_client_id>",
            "tenant_id": "<sharepoint_app_tenant_id>",
            "thumbprint": "<sharepoint_app_cert_thumbprint>",
            "certificate": "path_to_private_cert_keyfile",
            "dataobjects": "Books",
        },
    }

    document = Document(
        base_uri="https://ametnes.sharepoint.com/sites/nesis-test/",
        document_id="edu323-23423-23frs-234232",
        filename="sharepoint_file.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={
            "file_name": "sharepoint_file.pdf",
            "file_url": "/sites/nesit-test/Shared Documents/sharepoint_file.pdf",
            "etag": "edu323-23423-23frs-234232",
            "size": 1023,
            "author": "author_name",
            "last_modified": "2024-01-10 06:40:07",
        },
        last_modified=datetime.datetime.utcnow(),
    )

    session.add(document)
    session.commit()

    sp_client_context = mock.MagicMock()
    root_folder = mock.MagicMock()

    file_mock = mock.MagicMock()
    _folders = mock.MagicMock()

    sharepoint_context().with_client_certificate.return_value = sp_client_context

    sp_client_context.web.default_document_library.return_value.root_folder = (
        root_folder
    )

    type(file_mock).name = mock.PropertyMock(return_value="sharepoint_file.pdf")
    type(file_mock).serverRelativeUrl = mock.PropertyMock(
        return_value=r"/sites/nesit-test/Shared Documents/sharepoint_file.pdf"
    )
    type(file_mock).unique_id = mock.PropertyMock(
        return_value="edu323-23423-23frs-234232"
    )
    type(file_mock).time_last_modified = mock.PropertyMock(
        return_value=datetime.datetime.strptime(
            "2024-04-10 06:40:07", "%Y-%m-%d %H:%M:%S"
        )
    )
    type(file_mock).length = mock.PropertyMock(return_value=2023)
    type(file_mock).author = mock.PropertyMock(return_value="file author")

    root_folder.folders.get_by_path.return_value = _folders
    _folders.get_files.return_value.execute_query.return_value = [file_mock]

    file_download = mock.MagicMock()
    file_mock.download.return_value.execute_query.return_value = file_download

    http_client = mock.MagicMock()
    http_client.upload.return_value = json.dumps({})

    sharepoint.fetch_documents(
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
    assert file_path.endswith("sharepoint_file.pdf")
    assert field == "file"
    ut.TestCase().assertDictEqual(
        metadata,
        {
            "datasource": "documents",
            "file_name": "sharepoint_file.pdf",
            "self_link": r"https://ametnes.sharepoint.com/sites/nesit-test/Shared Documents/sharepoint_file.pdf",
        },
    )

    # The document has now been updated
    documents = session.query(Document).all()
    assert len(documents) == 1
    assert documents[0].store_metadata["last_modified"] == "2024-04-10 06:40:07"


@mock.patch("nesis.api.core.document_loaders.sharepoint.ClientContext")
def test_unsync_sharepoint_documents(
    sharepoint_context: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    """
    Test deleting of sharepoint documents from the rag engine if they have been deleted from sharepoint
    """
    data = {
        "name": "sharepoint documents",
        "engine": "sharepoint",
        "connection": {
            "endpoint": "https://ametnes.sharepoint.com/sites/nesis-test/",
            "client_id": "<sharepoint_app_client_id>",
            "tenant_id": "<sharepoint_app_tenant_id>",
            "thumbprint": "<sharepoint_app_cert_thumbprint>",
            "certificate": "path_to_private_cert_keyfile",
            "dataobjects": "Books",
        },
    }

    document = Document(
        base_uri="https://ametnes.sharepoint.com/sites/nesis-test/",
        document_id="edu323-23423-23frs",
        filename="Test_file.pdf",
        rag_metadata={"data": [{"doc_id": str(uuid.uuid4())}]},
        store_metadata={
            "file_name": "Test_file.pdf",
            "file_url": "/sites/nesit-test/Shared Documents/Test_file.pdf",
            "etag": "edu323-23423-23frs",
            "size": 1023,
            "author": "author_name",
            "last_modified": "2024-03-10 06:40:07",
        },
        last_modified=datetime.datetime.utcnow(),
    )

    session.add(document)
    session.commit()

    sp_client_context = mock.MagicMock()
    root_folder = mock.MagicMock()

    _folders = mock.MagicMock()

    sharepoint_context().with_client_certificate.return_value = sp_client_context

    sp_client_context.web.default_document_library.return_value.root_folder = (
        root_folder
    )

    root_folder.folders.get_by_path.return_value = _folders
    _folders.get_files.return_value.execute_query.return_value = []

    get_file_response = mock.MagicMock()
    sp_client_context.web.get_file_by_server_relative_url.return_value = (
        get_file_response
    )

    response_val = mock.MagicMock()
    type(response_val).status_code = mock.PropertyMock(return_value=404)

    get_file_response.get.return_value.execute_query.side_effect = (
        sharepoint.ClientRequestException(response=response_val)
    )

    http_client = mock.MagicMock()

    documents = session.query(Document).all()
    assert len(documents) == 1

    sharepoint.fetch_documents(
        connection=data["connection"],
        http_client=http_client,
        metadata={"datasource": "documents"},
        rag_endpoint="http://localhost:8080",
        cache_client=cache,
    )

    _, upload_kwargs = http_client.deletes.call_args_list[0]
    urls = upload_kwargs["urls"]

    assert (
        urls[0]
        == f"http://localhost:8080/v1/ingest/documents/{document.rag_metadata['data'][0]['doc_id']}"
    )
    documents = session.query(Document).all()
    assert len(documents) == 0
