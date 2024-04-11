import json
import os
import random
import uuid

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


def test_create_invalid_role(client):

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

    # Test duplicate role
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(role),
    )
    assert 409 == response.status_code, response.json

    # Test creating an invalid role with a string policy document
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(
            {
                **role,
                "name": str(uuid.uuid4()),
                "policy": json.dumps(role["policy"]) + "Some.Extra.String",
            }
        ),
    )
    assert 400 == response.status_code, response.json


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

    # Test creating a role with a string policy document
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(
            {**role, "name": str(uuid.uuid4()), "policy": json.dumps(role["policy"])}
        ),
    )
    assert 200 == response.status_code, response.json

    #
    # Get all roles. Should have 2 here
    response = client.get(
        f"/v1/roles", headers=tests.get_header(token=session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 2 == len(response.json["items"])

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

    # Create a role as a regular user, fails due to permissions
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

    # Admin creates the role
    roles_response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == roles_response.status_code, response.json

    # And assigns it to the user
    response = client.post(
        f"/v1/users/{regular_user['id']}/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(roles_response.json),
    )
    assert 200 == response.status_code, response.json

    # Getting that user's roles should return the created role
    response = client.get(
        f"/v1/users/{regular_user['id']}/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(roles_response.json),
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])

    role["name"] = (f"document-manager{random.randint(3, 19)}",)
    roles_response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == roles_response.status_code, response.json


def test_read_permitted_resources_as_user(client):
    """
    This tests that a user given read access to a specific datasource, will only be able to
    list/read from that since datasource
    :param client:
    :return:
    """

    # Create an admin user
    admin_session = tests.get_admin_session(app=client)

    # Create a datasource
    payload = {
        "type": "minio",
        "name": "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "host": "localhost",
            "port": "5432",
            "database": "initdb",
        },
    }

    # Create finance6 datasource
    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.json

    # Create finance7 datasource
    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({**payload, "name": "finance7"}),
    )
    assert 200 == response.status_code, response.json

    # A role allowing access to the finance6 datasource
    role = {
        "name": f"document-manager{random.randint(3, 19)}",
        "policy": {
            "items": [
                {"action": "read", "resource": "datasources/finance6"},
            ]
        },
    }
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == response.status_code, response.json

    # Admin creates a regular user assigning them access to the finance6 datasource
    user_data = {
        "name": "Test User",
        "email": "another.user@domain.com",
        "password": "password",
        "roles": [response.json["id"]],
        "enabled": True,
    }

    response = client.post(
        f"/v1/users",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(user_data),
    )
    assert 200 == response.status_code, response.json

    user_session = client.post(
        f"/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps(user_data),
    ).json
    assert 200 == response.status_code, response.json

    get_datasources = client.get(
        f"/v1/datasources",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(user_data),
    ).json

    assert 1 == len(
        get_datasources["items"]
    ), f"Expected 1 datasource by received {len(get_datasources.json['items'])}"
