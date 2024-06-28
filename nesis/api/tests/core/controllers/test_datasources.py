import json

import yaml

import unittest as ut

import pytest

from sqlalchemy.orm.session import Session
from nesis.api.core.controllers import app as cloud_app
import nesis.api.tests as tests
import nesis.api.core.services as services
from nesis.api.core.models import initialize_engine, DBSession


@pytest.fixture
def client():

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    services.init_services(tests.config)
    return cloud_app.test_client()


@pytest.fixture
def tc():
    return ut.TestCase()


def get_admin_session(client):
    admin_data = {
        "name": "s3 documents",
        "password": tests.admin_password,
        "email": tests.admin_email,
    }
    # Create an admin user
    return client.post(
        f"/v1/sessions", headers=tests.get_header(), data=json.dumps(admin_data)
    ).json


def test_create_datasource_invalid_input(client, tc):
    # Get the prediction
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

    admin_session = get_admin_session(client=client)

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({}),
    )
    assert 400 == response.status_code, response.json

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({"name": "Bad Name"}),
    )
    assert 400 == response.status_code, response.json

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({"name": "good-name"}),
    )
    assert 400 == response.status_code, response.json

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({"name": "good-name", "type": "type"}),
    )
    assert 400 == response.status_code, response.json

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({**payload, "connection": {}}),
    )
    assert 400 == response.status_code, response.json
    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({**payload, "connection": None}),
    )
    assert 400 == response.status_code, response.json


def test_create_datasource(client, tc):
    # Get the prediction
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

    admin_session = get_admin_session(client=client)

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.json

    # Duplicate datasource name should be rejected as a conflict
    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 409 == response.status_code
    assert "exists" in response.json["message"]

    # Test that we have only the one datasource
    response = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    print(response.json)
    assert 1 == len(response.json["items"])

    # Retrieve the datasource by id
    datasource_id = response.json["items"][0]["id"]
    response = client.get(
        f"/v1/datasources/{datasource_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.json
    print(response.json)
    assert response.json.get("connection") is not None

    # When we delete the datasource, is it really gone?
    response = client.delete(
        f"/v1/datasources/{datasource_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.json

    response = client.get(
        f"/v1/datasources/{datasource_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 404 == response.status_code, response.json


def test_update_datasource(client, tc):
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

    admin_session = get_admin_session(client=client)

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.json
    assert response.json.get("connection") is not None
    print(json.dumps(response.json["connection"]))

    response = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    print(response.json)
    assert 1 == len(response.json["items"])

    datasource_id = response.json["items"][0]["id"]

    response = client.get(
        f"/v1/datasources/{datasource_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.json

    datasource = response.json

    datasource["connection"] = {
        "user": "root",
        "password": "some.password",
        "endpoint": "some.other.host.tld",
        "dataobjects": "initdb",
    }

    response = client.put(
        f"/v1/datasources/{datasource_id}",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(datasource),
    )
    assert 200 == response.status_code, response.json

    response = client.get(
        f"/v1/datasources/{datasource_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )

    # Datasource password is never emitted so we skip it
    tc.assertDictEqual(
        response.json["connection"],
        {k: v for k, v in datasource["connection"].items() if k != "password"},
    )


def test_create_datasource_schedule(client, tc):
    # Get the prediction
    payload = {
        "type": "minio",
        "name": "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
        "schedule": "Some invalid schedule",
    }

    admin_session = get_admin_session(client=client)

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 400 == response.status_code, response.json

    # Test that we have only the one datasource
    response = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 0 == len(response.json["items"])

    payload["schedule"] = "*/5 * * * *"
    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text

    # Test that we have only the one datasource
    response = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])

    # Test that we have only the one task
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])


def test_update_datasource_schedule(client, tc):
    # Get the prediction
    payload = {
        "type": "minio",
        "name": "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
        "schedule": "*/5 * * * *",
    }

    admin_session = get_admin_session(client=client)

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.json

    # We update the schedule
    datasource = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    ).json["items"][0]

    datasource["schedule"] = "*/10 * * * *"

    response = client.put(
        f"/v1/datasources/{datasource['id']}",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(datasource),
    )
    assert 200 == response.status_code, response.json

    # Test that we have only the one task
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])
    assert response.json["items"][0]["schedule"] == datasource["schedule"]


def test_delete_datasource_schedule(client, tc):
    # This test focuses on the delete functionality. We want to ensure that when a datasource is deleted, all
    # corresponding tasks are delete too
    payload = {
        "type": "minio",
        "name": "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
        "schedule": "*/5 * * * *",
    }

    admin_session = get_admin_session(client=client)

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text
    datasource = response.json

    # Test that we have only the one datasource
    response = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])

    # Test that we have only the one task
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])

    #
    # Delete the datasource
    response = client.delete(
        f"/v1/datasources/{datasource['id']}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.json

    response = client.get(
        "/v1/datasources", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 0 == len(response.json["items"])

    # Test that we have only the one task
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 0 == len(response.json["items"])
