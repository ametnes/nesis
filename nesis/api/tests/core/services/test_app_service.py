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
    create_datasource,
    create_user,
    create_prediction,
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
    # Create a datasource admin role
    role = {
        "name": f"user-admin-{uuid.uuid4()}",
        "policy": {
            "items": [
                {"action": "create", "resource": "roles/*"},
                {"action": "create", "resource": "users/*"},
            ]
        },
    }
    app = _create_app(role=role)
    assert app.id is not None
    assert app.uuid is not None
    assert app.secret is not None

    encoded_secret = base64.b64decode(app.secret).decode("utf-8")
    encoded_secret_parts = encoded_secret.split(":")

    assert encoded_secret_parts[0] == app.uuid

    return app


def _create_app(role: dict = None):
    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )

    role_record = None
    if role:
        # admin creates the role
        role_record = create_role(
            service=services.role_service, role=role, token=admin_user.token
        )
    app: App = create_app(
        token=admin_user.token,
        name=f"some-integration-{uuid.uuid4()}",
        role_ids=[role_record.uuid] if role_record else [],
    )
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
    role["name"] = "user-admin-3"
    create_role(
        service=services.role_service, role=role, token=app2.secret.decode("utf-8")
    )

    # Create a datasource without the right permission
    with pytest.raises(PermissionException) as ex_info:
        create_datasource(
            token=app2.secret.decode("utf-8"),
            service=services.datasource_service,
            name=f"datasource-{uuid.uuid4()}",
        )
        assert (
            "Not authorized to perform CREATE on DATASOURCES".lower()
            in str(ex_info).lower()
        )

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )

    # Assign a datasource policy to the app and the app can create a datasource
    datasource_policy = {
        "name": "datasource_policy",
        "policy": {
            "items": [
                {"action": "create", "resource": "datasources/*"},
            ]
        },
    }

    datasource_role = create_role(
        service=services.role_service,
        role=datasource_policy,
        token=app2.secret.decode("utf-8"),
    )
    assign_role_to_app(
        service=services.app_service,
        token=admin_user.token,
        role=datasource_role.to_dict(),
        app_id=app2.uuid,
    )
    create_datasource(
        token=app2.secret.decode("utf-8"),
        service=services.datasource_service,
        name=f"datasource-{uuid.uuid4()}",
    )


def test_app_user_session(http_client, tc):
    app: App = test_create_app(http_client=http_client, tc=tc)

    app_api_key = app.secret.decode("utf-8")

    # Create an admin session
    admin_user_session = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )
    datasource = create_datasource(
        token=admin_user_session.token,
        service=services.datasource_service,
        name=f"datasource-{uuid.uuid4()}",
    )

    # Create a datasource without the right permission
    with pytest.raises(PermissionException) as ex_info:
        create_prediction(
            token=app.secret.decode("utf-8"),
            service=services.qanda_prediction_service,
            query="What is nesis?",
        )
    assert (
        "Not authorized to perform CREATE on PREDICTIONS".lower()
        in str(ex_info).lower()
    )

    """
    Now we create a user with permissions to create a prediction. Then we create a prediction using the app token
    (that does not have any role assigned to it).
    We then create a prediction using the app token combined with the user_id
    """

    # Assign a datasource policy to the app and the app can create a datasource
    datasource_policy = {
        "name": "datasource_policy",
        "policy": {
            "items": [
                {"action": "create", "resource": "predictions/*"},
                {"action": "read", "resource": "datasources/*"},
            ]
        },
    }

    datasource_role = create_role(
        service=services.role_service,
        role=datasource_policy,
        token=admin_user_session.token,
    )

    # Create a new user
    new_user = create_user(
        service=services.user_service,
        email="some.other.email@domain.com",
        password=tests.admin_password,
        token=admin_user_session.token,
        role_ids=[datasource_role.uuid],
    )

    http_client.post.side_effect = [json.dumps({"response": "the response"})]
    # Create the user session
    prediction = create_prediction(
        token=app.secret.decode("utf-8"),
        service=services.qanda_prediction_service,
        query="What is nesis?",
        user_id=new_user.uuid,
    )

    assert prediction.id is not None
    assert prediction.uid is not None
