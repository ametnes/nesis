import unittest as ut
import uuid
from unittest import mock

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.tests as tests
from nesis.api.core.models import initialize_engine, DBSession
from nesis.api.core.models.entities import Datasource
from nesis.api.core.tasks.document_management import ingest_datasource
from nesis.api.core.util import http
from nesis.api.tests.core.services import (
    create_user_session,
)


@pytest.fixture
def tc():
    return ut.TestCase()


@pytest.fixture
def cache_client() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture
def http_client() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture(autouse=True)
def setup():

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    services.init_services(
        config=tests.config, http_client=http.HttpClient(config=tests.config)
    )
    # Clear all jobs first
    services.task_service._scheduler.remove_all_jobs()


def create_datasource(token: str, datasource_type: str) -> Datasource:
    payload = {
        "type": datasource_type,
        "name": str(uuid.uuid4()),
        "connection": {
            "user": "caikuodda",
            "password": "password",
            "host": "localhost",
            "endpoint": "localhost",
            "port": "5432",
            "database": "initdb",
        },
    }

    return services.datasource_service.create(datasource=payload, token=token)


@mock.patch("nesis.api.core.tasks.document_management.s3_documents")
def test_ingest_datasource_minio(
    s3_documents: mock.MagicMock, tc, cache_client, http_client
):
    """
    Test the ingestion happy path
    """

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )
    datasource: Datasource = create_datasource(
        token=admin_user.token, datasource_type="minio"
    )

    ingest_datasource(
        config=tests.config,
        http_client=http_client,
        cache_client=cache_client,
        params={"datasource": {"id": datasource.uuid}},
    )

    _, kwargs_fetch_documents = s3_documents.fetch_documents.call_args_list[0]
    assert kwargs_fetch_documents["rag_endpoint"] == tests.config["rag"]["endpoint"]
    tc.assertDictEqual(kwargs_fetch_documents["connection"], datasource.connection)
    tc.assertDictEqual(
        kwargs_fetch_documents["metadata"], {"datasource": datasource.name}
    )


@mock.patch("nesis.api.core.tasks.document_management.samba")
@mock.patch("nesis.api.core.document_loaders.samba.scandir")
def test_ingest_datasource_samba(
    scandir, samba: mock.MagicMock, tc, cache_client, http_client
):
    """
    Test the ingestion happy path
    """

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )
    datasource: Datasource = create_datasource(
        token=admin_user.token, datasource_type="windows_share"
    )

    ingest_datasource(
        config=tests.config,
        http_client=http_client,
        cache_client=cache_client,
        params={"datasource": {"id": datasource.uuid}},
    )

    _, kwargs_fetch_documents = samba.fetch_documents.call_args_list[0]
    assert kwargs_fetch_documents["rag_endpoint"] == tests.config["rag"]["endpoint"]
    tc.assertDictEqual(kwargs_fetch_documents["connection"], datasource.connection)
    tc.assertDictEqual(
        kwargs_fetch_documents["metadata"], {"datasource": datasource.name}
    )


@mock.patch("nesis.api.core.tasks.document_management.samba")
@mock.patch("nesis.api.core.document_loaders.samba.scandir")
def test_ingest_datasource_invalid_datasource(
    scandir, samba: mock.MagicMock, tc, cache_client, http_client
):

    # An invalid datasource should raise an error
    with pytest.raises(ValueError) as ex_info:
        ingest_datasource(
            config=tests.config,
            http_client=http_client,
            cache_client=cache_client,
            params={"datasource": {"id": str(uuid.uuid4())}},
        )
        assert "Invalid datasource" in str(ex_info)
