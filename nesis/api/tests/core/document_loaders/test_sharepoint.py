import json
import os
import datetime
import uuid

import unittest as ut
import unittest.mock as mock

from sqlalchemy.orm.session import Session

from office365.sharepoint.files.system_object_type import FileSystemObjectType

import nesis.api.core.document_loaders.sharepoint as sharepoint
from nesis.api import tests
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine
import nesis.api.core.services as services
from nesis.api.core.models.entities import (
    Datasource,
    DatasourceType,
    DatasourceStatus,
)


@mock.patch("nesis.api.core.document_loaders.sharepoint.ClientContext")
def test_fetch_documents(
    client_context: mock.MagicMock, cache: mock.MagicMock, session: Session
) -> None:
    data = {
        "name": "sharepoint documents",
        "engine": "sharepoint",
        "connection": {
            "site_url": "https://ametnes.sharepoint.com/sites/nesis-test/",
            "client_id": "<sharepoint_app_client_id>",
            "tenant": "<sharepoint_app_tenant_id>",
            "thumbprint": "<sharepoint_app_cert_thumbprint>",
            "certificate_path": "path_to_private_cert_keyfile",
            "data_objects": "Books, Contracts",
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
    document_library = mock.MagicMock()
    item = mock.MagicMock()
    file_mock = mock.MagicMock()
    _items = mock.MagicMock()

    client_context().with_client_certificate.return_value = sp_client_context

    sp_client_context.web.default_document_library.return_value = document_library

    type(file_mock).name = mock.PropertyMock(return_value="some_file.pdf")
    type(file_mock).serverRelativeUrl = mock.PropertyMock(
        return_value=r"/sites/nesit-test/Shared Documents/some_file.pdf"
    )
    type(file_mock).unique_id = mock.PropertyMock(return_value="123123-123131-1313")
    type(file_mock).last_time_last_modified = mock.PropertyMock(
        return_value=datetime.time()
    )
    type(file_mock).length = mock.PropertyMock(return_value=1023)
    type(file_mock).author = mock.PropertyMock(return_value="file author")

    type(item).file_system_object_type = mock.PropertyMock(return_value=0)
    type(item).file = mock.PropertyMock(return_value=file_mock)
    document_library.items = _items

    document_library.items.select.return_value.expand.return_value.get_all.return_value.execute_query.return_value = [
        item
    ]

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
            "self_link": r"/sites/nesit-test/Shared Documents/some_file.pdf",
        },
    )


class SharepointTest(ut.TestCase):

    def setUp(self) -> None:
        self.http_client = mock.MagicMock()
        # self.http_client = http.HttpClient()
        # document_management._minio_client = mock.MagicMock()

        os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1"

        self.config = tests.config
        initialize_engine(self.config)
        self.session: Session = DBSession()
        tests.clear_database(self.session)

        os.environ["OPENAI_API_KEY"] = "<open-api-key>"

        os.environ["OPTIMAI_ADMIN_EMAIL"] = "<username>"
        os.environ["OPTIMAI_ADMIN_PASSWORD"] = "<password>"

        services.init_services(self.config)

    def test_fetch_sharepoint_documents(self) -> None:
        data = {
            "name": "sharepoint documents",
            "engine": "sharepoint",
            "connection": {
                "site_url": "https://ametnes.sharepoint.com/sites/nesis-test/",
                "client_id": "<sharepoint_app_client_id>",
                "tenant": "<sharepoint_app_tenant_id>",
                "thumbprint": "<sharepoint_app_cert_thumbprint>",
                "certificate_path": "path_to_private_cert_keyfile",
                "data_objects": "Books, Contracts",
            },
        }

        datasource = Datasource(
            name=data["name"],
            connection=data["connection"],
            source_type=DatasourceType.SHAREPOINT,
            status=DatasourceStatus.ONLINE,
        )

        self.session.add(datasource)
        self.session.commit()

        endpoint = (
            "https://resource-6159823050-privategpt.dev-accounts.ametnes.net/v1/ingest"
        )

        metadata = {}

        sharepoint.fetch_documents(
            connection=data["connection"],
            http_client=self.http_client,
            rag_endpoint=endpoint,
            metadata=metadata,
            cache_client=mock.MagicMock(),
        )
