import json
import os
import random

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.tests as tests
from nesis.api.core.controllers import app as cloud_app
from nesis.api.core.models import initialize_engine, DBSession

"""
This file contains all tests for datasource roles and permissions
"""


@pytest.fixture
def client():

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)
    return cloud_app.test_client()


def test_read_permissions(client):
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
            "endpoint": "localhost",
            "dataobjects": "initdb",
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


def test_delete_permissions(client):
    """
    This tests that a user given delete access to a specific datasource, will only be able to
    delete that since datasource
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
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
    }

    # Create finance6 datasource
    datasource1 = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    ).json

    # Create finance7 datasource
    datasource2 = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({**payload, "name": "finance7"}),
    ).json

    # A role allowing access to the finance6 datasource
    role = {
        "name": f"document-manager{random.randint(3, 19)}",
        "policy": {
            "items": [
                {"action": "read", "resource": f"datasources/{datasource1['name']}"},
                {"action": "read", "resource": f"datasources/{datasource2['name']}"},
                {"action": "delete", "resource": f"datasources/{datasource2['name']}"},
            ]
        },
    }
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == response.status_code, response.json

    # Admin creates a regular user assigning them access to the datasources
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

    # Log in as the regular user
    user_session = client.post(
        f"/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps(user_data),
    ).json
    assert 200 == response.status_code, response.json

    # Delete the datasource1. Should fail
    response = client.delete(
        f"/v1/datasources/{datasource1['id']}",
        headers=tests.get_header(token=user_session["token"]),
    )
    assert 403 == response.status_code, response.json

    # Get the datasources. Expect the two to exist
    get_datasources = client.get(
        f"/v1/datasources", headers=tests.get_header(token=user_session["token"])
    ).json
    assert 2 == len(
        get_datasources["items"]
    ), f"Expected 2 datasource but received {len(get_datasources.json['items'])}"

    # Delete the datasource2. Should succeed
    response = client.delete(
        f"/v1/datasources/{datasource2['id']}",
        headers=tests.get_header(token=user_session["token"]),
    )
    assert 200 == response.status_code, response.json

    get_datasources = client.get(
        f"/v1/datasources", headers=tests.get_header(token=user_session["token"])
    ).json
    assert 1 == len(
        get_datasources["items"]
    ), f"Expected 2 datasource but received {len(get_datasources.json['items'])}"
    assert get_datasources["items"][0]["name"] == datasource1["name"]


def test_update_permissions(client):
    """
    This tests that a user given update access to a specific datasource, will only be able to
    update that since datasource
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
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
    }

    # Create finance6 datasource
    datasource1 = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    ).json

    # Create finance7 datasource
    datasource2 = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({**payload, "name": "finance7"}),
    ).json

    # A role allowing access to the finance6 datasource
    role = {
        "name": f"document-manager{random.randint(3, 19)}",
        "policy": {
            "items": [
                {"action": "read", "resource": f"datasources/{datasource1['name']}"},
                {"action": "read", "resource": f"datasources/{datasource2['name']}"},
                {"action": "update", "resource": f"datasources/{datasource2['name']}"},
            ]
        },
    }
    response = client.post(
        f"/v1/roles",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(role),
    )
    assert 200 == response.status_code, response.json

    # Admin creates a regular user assigning them access to the datasources
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

    # Log in as the regular user
    user_session = client.post(
        f"/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps(user_data),
    ).json
    assert 200 == response.status_code, response.json

    # Update the datasource1. Should fail
    response = client.put(
        f"/v1/datasources/{datasource1['id']}",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps({**datasource1, "type": "postgres"}),
    )
    assert 403 == response.status_code, response.json

    # Get the datasources. Expect the datasource unch
    got_datasource = client.get(
        f"/v1/datasources/{datasource1['id']}",
        headers=tests.get_header(token=user_session["token"]),
    ).json
    assert got_datasource["type"] == payload["type"]

    # Update the datasource2. Should succeed
    response = client.put(
        f"/v1/datasources/{datasource2['id']}",
        headers=tests.get_header(token=user_session["token"]),
        data=(json.dumps({**datasource2, "type": "postgres"})),
    )
    assert 200 == response.status_code, response.json

    got_datasource = client.get(
        f"/v1/datasources/{datasource2['id']}",
        headers=tests.get_header(token=user_session["token"]),
    ).json
    assert got_datasource["type"] == "postgres"
