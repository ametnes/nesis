import json
import unittest as ut
import uuid
from unittest import mock

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.tests as tests
from nesis.api.core.controllers import app as cloud_app
from nesis.api.core.models import initialize_engine, DBSession


@pytest.fixture
def http_client():
    return mock.MagicMock()


@pytest.fixture
def tc():
    return ut.TestCase()


@pytest.fixture
def client(http_client):

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    services.init_services(tests.config, http_client=http_client)
    return cloud_app.test_client()


def create_app(client, session, roles=None):
    payload = {
        "name": "finance6",
        "roles": roles,
    }

    response = client.post(
        f"/v1/apps",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text
    return response.json


def test_create_app(client, http_client, tc):
    """
    Create an app with create permission on users and roles
    """
    admin_session = tests.get_admin_session(app=client)
    role = {
        "name": f"user-admin-{uuid.uuid4()}",
        "policy": {
            "items": [
                {"action": "create", "resource": "roles/*"},
                {"action": "create", "resource": "users/*"},
            ]
        },
    }
    role_result = tests.create_role(client=client, session=admin_session, role=role)
    app = create_app(client=client, session=admin_session, roles=[role_result["id"]])

    assert app.get("id") is not None
    # The secret is shown just this once and the user must save it somewhere safe
    assert app.get("secret") is not None

    # The app is now able to create a role
    role_result = tests.create_role(
        client=client,
        session={"token": app["secret"]},
        role={**role, "name": f"user-admin-{uuid.uuid4()}"},
    )
    assert role_result.get("id") is not None

    """
    # Just a quick test that get works and returns all available apps
    """
    response = client.get(
        f"/v1/apps",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text
    assert 1 == len(response.json["items"])

    # Ensure secrets are not leaked back to the user
    assert response.json["items"][0].get("secret") is None

    """
    If app is deleted, we should not be able to perform any action as the app
    """
    response = client.delete(
        f"/v1/apps/{app['id']}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text
    # Ensure no records exist
    response = client.get(
        f"/v1/apps",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text
    assert 0 == len(response.json["items"])

    # Now attempting to create a role as the app should fail with a permission error
    role_result = tests.create_role(
        client=client,
        session={"token": app["secret"]},
        role={**role, "name": f"user-admin-{uuid.uuid4()}"},
        expect=403,
    )

    assert role_result["message"] == "Not authorized to perform CREATE on ROLES"


def test_app_as_user(client, http_client, tc):
    """
    Create an app with create permission on users and roles
    """
    admin_session = tests.get_admin_session(app=client)
    role = {
        "name": f"user-admin-{uuid.uuid4()}",
        "policy": {
            "items": [
                {"action": "create", "resource": "predictions/*"},
                {"action": "read", "resource": "datasources/*"},
            ]
        },
    }

    datasource = {
        "type": "minio",
        "name": "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
    }
    tests.create_datasource(client=client, session=admin_session, datasource=datasource)
    role_result = tests.create_role(client=client, session=admin_session, role=role)
    app = create_app(client=client, session=admin_session)

    user_payload = {
        "name": "some name",
        "email": "some.other.email@domain.com",
        "password": tests.admin_password,
        "roles": [role_result["id"]],
    }

    # Create a user
    response = client.post(
        f"/v1/users",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(user_payload),
    )
    assert 200 == response.status_code, response.text
    user_result = response.json

    # Create a prediction without the user header, should fail with a 403
    http_client.post.side_effect = [json.dumps({"response": "the response"})] * 5
    response = client.post(
        "/v1/modules/qanda/predictions",
        headers=tests.get_header(token=app["secret"]),
        data=json.dumps({"query": "what do you know?"}),
    )
    assert 403 == response.status_code, response.text

    # Create a prediction with the user header, should succeed
    response = client.post(
        "/v1/modules/qanda/predictions",
        headers={
            **tests.get_header(token=app["secret"]),
            "X-Nesis-Request-UserKey": user_result["id"],
        },
        data=json.dumps({"query": "what do you know?"}),
    )
    assert 200 == response.status_code, response.text
    assert response.json["input"] == "what do you know?"
    tc.assertDictEqual(response.json["data"], {"response": "the response"})


def test_operate_app_roles(client, http_client, tc):
    """
    Test operations on a specific app.
    1. Add a role to an app
    2. Get an apps roles
    """
    admin_session = tests.get_admin_session(app=client)
    role = {
        "name": f"user-admin-{uuid.uuid4()}",
        "policy": {
            "items": [
                {"action": "create", "resource": "predictions/*"},
                {"action": "read", "resource": "datasources/*"},
            ]
        },
    }

    app = create_app(client=client, session=admin_session)

    # Get roles assigned to the app, expect count == 0
    response = client.get(
        f"/v1/apps/{app['id']}/roles",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text
    assert 0 == len(response.json["items"])

    role_result = tests.create_role(client=client, session=admin_session, role=role)
    response = client.post(
        f"/v1/apps/{app['id']}/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(role_result),
    )
    assert 200 == response.status_code, response.text

    # Get roles assigned to the app, expect count == 1
    response = client.get(
        f"/v1/apps/{app['id']}/roles",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text
    assert 1 == len(response.json["items"])
