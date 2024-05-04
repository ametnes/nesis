import json
import os
import uuid

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
        "name": "Full Name",
        "password": tests.admin_password,
        "email": tests.admin_email,
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


def test_create_user_oauth(client):
    # Test that if authentication with oauth key/value pair

    oauth_token_key = "____nesis_test_oath_key___"
    oauth_token_value = str(uuid.uuid4())
    os.environ["NESIS_OAUTH_TOKEN_KEY"] = oauth_token_key
    os.environ["NESIS_OAUTH_TOKEN_VALUE"] = oauth_token_value

    user = test_create_user(client=client)

    data = {
        "name": "Full Name",
        "email": user["email"],
    }

    # No oauth tokens supplied and no password supplied, so we must fail
    response = client.post(
        "/v1/sessions", headers=tests.get_header(), data=json.dumps(data)
    )
    assert 401 == response.status_code
    assert response.json.get("token") is None

    # Invalid oauth tokens supplied and no password supplied so we must fail
    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps({**data, oauth_token_key: str(uuid.uuid4())}),
    )
    assert 401 == response.status_code
    assert response.json.get("token") is None

    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps({**data, oauth_token_key: oauth_token_value}),
    )
    assert 200 == response.status_code
    assert response.json.get("token") is not None

    admin_session = response.json

    # Now get the list of users, we should have just the one
    response = client.get(
        f"/v1/users", headers=tests.get_header(token=admin_session["token"])
    )
    assert 1 == len(response.json["items"])

    # Authenticate as another user
    response = client.post(
        "/v1/sessions",
        headers=tests.get_header(),
        data=json.dumps(
            {
                **data,
                oauth_token_key: oauth_token_value,
                "email": "another.user.email@domain.com",
            }
        ),
    )
    assert 200 == response.status_code
    assert response.json.get("token") is not None

    # Now get the list of users, we should have two users
    response = client.get(
        f"/v1/users", headers=tests.get_header(token=admin_session["token"])
    )
    assert 2 == len(response.json["items"])


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
