import base64
import json
import uuid
from typing import Optional, List

import yaml

import unittest as ut
import unittest.mock as mock

import pytest

from sqlalchemy.orm.session import Session
import nesis.api.tests as tests
import nesis.api.core.services as services
from nesis.api.core.models import initialize_engine, DBSession
from nesis.api.core.models.entities import Datasource, App
from nesis.api.core.services import PermissionException
from nesis.api.tests.core.services import (
    create_user_session,
    create_role,
    assign_role_to_user,
    assign_role_to_app,
)


@pytest.fixture
def http_client():
    return mock.MagicMock()


@pytest.fixture
def tc():
    return ut.TestCase()


@pytest.fixture(autouse=True)
def setup(http_client):

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    services.init_services(config=tests.config, http_client=http_client)


def create_app(token: str, name: str, role_ids: Optional[List[str]]) -> App:
    payload = {"name": name, "roles": role_ids}

    return services.app_service.create(app=payload, token=token)


def test_create_app(http_client, tc):
    """
    Test the datasource happy path
    """

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )

    # Create a datasource admin role
    role = {
        "name": "user-admin",
        "policy": {
            "items": [
                {"action": "create", "resource": "roles/*"},
                {"action": "create", "resource": "users/*"},
            ]
        },
    }

    # admin creates the role
    role_record = create_role(
        service=services.role_service, role=role, token=admin_user.token
    )

    app: App = create_app(
        token=admin_user.token, name="some integration", role_ids=[role_record.uuid]
    )
    assert app.id is not None
    assert app.uuid is not None
    assert app.secret is not None

    encoded_secret = base64.b64decode(app.secret).decode("utf-8")
    encoded_secret_parts = encoded_secret.split(":")

    assert encoded_secret_parts[0] == app.uuid

    return app


def test_app_session(http_client, tc):
    app: App = test_create_app(http_client=http_client, tc=tc)

    app_api_key = app.secret.decode("utf-8")
    services.user_session_service.get(token=app_api_key)

    role = {
        "name": "user-admin-2",
        "policy": {
            "items": [
                {"action": "create", "resource": "roles/*"},
                {"action": "create", "resource": "users/*"},
            ]
        },
    }

    # api key creates the role
    create_role(service=services.role_service, role=role, token=app_api_key)

    app2: App = test_create_app(http_client=http_client, tc=tc)
    create_role(
        service=services.role_service, role=role, token=app2.secret.decode("utf-8")
    )

    # create_datasource()
