import json
import os
import random

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.tests as tests
from nesis.api.core.controllers import app as cloud_app
from nesis.api.core.models import initialize_engine, DBSession


@pytest.fixture
def client():

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)
    return cloud_app.test_client()


def test_create_role(client):

    session = tests.get_admin_session(app=client)

    # A role
    role = {
        "name": "document-manager",
        "policy": {"items": [{"action": "read", "resource": "users"}]},
    }
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(role),
    )
    assert 200 == response.status_code, response.json
    print(json.dumps(response.json))
    #
    # All retried users should not have their passwords exposed
    response = client.get(
        f"/v1/roles", headers=tests.get_header(token=session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])

    response = client.get(
        f"/v1/roles/{response.json['items'][0]['id']}",
        headers=tests.get_header(token=session["token"]),
    )
    assert 200 == response.status_code, response.json
    print(response.json)

    return response.json


def test_create_role_as_user(client):

    # Create an admin user
    admin_session = tests.get_admin_session(app=client)

    user_data = {
        "name": "s3 documents 1",
        "password": "password",
        "email": "some.email2@domain.com",
    }

    # Admin creates a regular user
    regular_user = client.post(
        f"/v1/users",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(user_data),
    ).json
    user_session = client.post(
        f"/v1/sessions", headers=tests.get_header(), data=json.dumps(user_data)
    ).json

    # A role as a regular user
    role = {
        "name": f"document-manager{random.randint(3, 19)}",
        "policy": {"items": [{"action": "create", "resource": "roles"}]},
    }
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(role),
    )
    assert 403 == response.status_code, response.json

    roles_response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == roles_response.status_code, response.json

    response = client.post(
        f"/v1/users/{regular_user['id']}/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(roles_response.json),
    )
    assert 200 == response.status_code, response.json

    role["name"] = (f"document-manager{random.randint(3, 19)}",)
    roles_response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == roles_response.status_code, response.json

    print(json.dumps(response.json))
