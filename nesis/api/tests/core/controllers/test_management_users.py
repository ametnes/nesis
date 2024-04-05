import json
import os

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.tests as tests
from nesis.api.core.controllers import app as cloud_app
from nesis.api.core.models import initialize_engine, DBSession


@pytest.fixture
def client():
    os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1"

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)
    return cloud_app.test_client()


def test_create_user(client):
    # Get the prediction
    data = {
        "name": "s3 documents",
        "password": tests.admin_password,
        "email": tests.admin_email,
        "root": True,
    }

    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps({**data, "password": "te"}),
    )
    assert 401 == response.status_code
    session = response.json

    response = client.post(
        "/v1/sessions", headers=tests.get_header(), data=json.dumps(data)
    )
    assert 200 == response.status_code
    session = response.json

    # A duplicate user should fail with conflict
    response = client.post(
        f"/v1/users",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(data),
    )
    assert 409 == response.status_code
    print(json.dumps(response.json))

    # All retried users should not have their passwords exposed
    response = client.get(
        f"/v1/users", headers=tests.get_header(token=session["token"])
    )
    assert 1 == len(response.json["items"])

    assert response.json["items"][0].get("password") is None

    response = client.get(
        f"/v1/users/{response.json['items'][0]['id']}",
        headers=tests.get_header(token=session["token"]),
    )
    assert data["email"] == response.json["email"]
    assert response.json.get("password") is None

    return response.json


def test_create_users(client):
    # Get the prediction
    user = test_create_user(client=client)
    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps({**user, "password": "password"}),
    )
    session = response.json

    # No auth token supplied
    response = client.post(
        "/v1/users",
        headers=tests.get_header(),
        data=json.dumps({**user, "email": "email@domain.com", "password": "asd"}),
    )
    assert 401 == response.status_code, response.json

    # User should not be root
    response = client.post(
        "/v1/users",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps({**user, "email": "email@domain.com", "password": "test"}),
    )
    assert 200 == response.status_code, response.json
    assert not response.json["root"]

    # We should have two users now
    response = client.get(
        f"/v1/users", headers=tests.get_header(token=session["token"])
    )
    assert 2 == len(response.json["items"])


def test_delete_user(client):
    # Get the prediction
    user = test_create_user(client=client)

    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps({**user, "password": "password"}),
    )
    session = response.json

    # Create user
    response = client.post(
        f"/v1/users",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(
            {
                "name": "Second User",
                "password": tests.admin_password,
                "email": f"user.{tests.admin_email}",
            }
        ),
    )
    assert 200 == response.status_code, response.json

    user = response.json

    # Delete user
    response = client.delete(f"/v1/users/{user['id']}", headers=tests.get_header())
    assert 401 == response.status_code, response.json

    response = client.delete(
        f"/v1/users/{user['id']}", headers=tests.get_header(token=session["token"])
    )
    assert 200 == response.status_code, response.json

    # Get user
    response = client.get(
        f"/v1/users/{user['id']}", headers=tests.get_header(token=session["token"])
    )
    assert 404 == response.status_code, response.json


def test_update_user(client):
    # Get the prediction
    user = test_create_user(client=client)

    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps({**user, "password": "password"}),
    )
    session = response.json

    # Update user
    new_email = "new.email@domain.com"
    response = client.put(
        f"/v1/users/{user['id']}",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps({**user, "email": new_email}),
    )
    assert 200 == response.status_code, response.json
    print(json.dumps(response.json))

    response = client.get(
        f"/v1/users/{user['id']}", headers=tests.get_header(token=session["token"])
    )
    assert new_email == response.json["email"]
