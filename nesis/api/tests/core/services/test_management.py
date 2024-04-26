import json
import uuid

import yaml

import unittest as ut
import unittest.mock as mock

import pytest

from sqlalchemy.orm.session import Session
import nesis.api.tests as tests
import nesis.api.core.services as services
from nesis.api.core.models import initialize_engine, DBSession
from nesis.api.core.models.entities import Datasource
from nesis.api.core.services import PermissionException
from nesis.api.tests.core.services import (
    create_user_session,
    create_role,
    assign_role,
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


def create_datasource(token: str, name: str = None) -> Datasource:
    payload = {
        "type": "minio",
        "name": name or "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
    }

    return services.datasource_service.create(datasource=payload, token=token)


def test_datasource_permissions(http_client, tc):
    """
    Test the datasource happy path
    """

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )
    datasource: Datasource = create_datasource(token=admin_user.token)
    assert datasource.id is not None
    assert datasource.uuid is not None

    a_given_user = {
        "email": "some.user@somedomain.com",
        "password": "some.password",
        "name": "Some Name",
    }
    given_user_record = services.user_service.create(
        user=a_given_user, token=admin_user.token
    )
    assert given_user_record.id is not None
    assert given_user_record.uuid is not None

    given_user_session = create_user_session(
        service=services.user_session_service,
        email=a_given_user["email"],
        password=a_given_user["password"],
    )

    # User should not be able to perform this action
    with pytest.raises(PermissionException) as ex_info:
        create_datasource(token=given_user_session.token)
        assert "Not authorized to perform this action" in str(ex_info)

    # Create a datasource admin role
    role = {
        "name": "datasource-admin",
        "policy": {
            "items": [
                {"action": "create", "resource": "roles/*"},
                {"action": "create", "resource": "datasources/*"},
            ]
        },
    }

    # user cannot create a role
    with pytest.raises(PermissionException) as ex_info:
        create_role(
            service=services.role_service, role=role, token=given_user_session.token
        )
        assert "Not authorized to perform this action" in str(ex_info)

    # admin creates the role
    role_record = create_role(
        service=services.role_service, role=role, token=admin_user.token
    )
    assign_role(
        service=services.user_role_service,
        token=admin_user.token,
        role=role_record.to_dict(),
        user_id=given_user_record.uuid,
    )

    # User can now create a datasource
    datasource_name = str(uuid.uuid4())
    datasource: Datasource = create_datasource(
        token=given_user_session.token, name=datasource_name
    )
    assert datasource.id is not None

    # User can also create a role
    role_record = create_role(
        service=services.role_service,
        role={**role, "name": f'{role["name"]}-{uuid.uuid4()}'},
        token=given_user_session.token,
    )
    assert role_record.id is not None
