import json
import unittest as ut

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.tests as tests
from nesis.api.core.controllers import app as cloud_app
from nesis.api.core.models import initialize_engine, DBSession

"""
This test runs all tests as administrator. The _permissions.py test module contains all tests with permission
"""


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


def create_datasource(client, session):
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

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text
    return response.json


def test_create_task_invalid_input(client, tc):

    admin_session = tests.get_admin_session(app=client)

    # Missing task type
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(),
        data=json.dumps({}),
    )
    assert 401 == response.status_code, response.text
    assert "Unauthorized" in response.text

    # Missing task type
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({}),
    )
    assert 400 == response.status_code, response.text
    assert "Invalid task type" in response.text

    # Missing task definition
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({"type": "ingest_datasource", "schedule": "Bad Schedul"}),
    )
    assert 400 == response.status_code, response.text
    assert "Task definition must be supplied" in response.text

    # Invalid datasource id
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(
            {
                "type": "ingest_datasource",
                "definition": {"datasource": {"id": "id"}},
            }
        ),
    )
    assert 400 == response.status_code, response.text
    assert "Invalid datasource" in response.text

    # Invalid schedule
    datasource = create_datasource(client=client, session=admin_session)
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(
            {
                "type": "ingest_datasource",
                "schedule": "Bad Schedul",
                "definition": {"datasource": {"id": datasource["id"]}},
            }
        ),
    )
    assert 400 == response.status_code, response.text
    assert "Invalid schedule" in response.text


def test_create_task(client, tc):

    admin_session = tests.get_admin_session(app=client)

    datasource = create_datasource(client=client, session=admin_session)
    payload = {
        "type": "ingest_datasource",
        "schedule": "2 4 * * mon,fri",
        "definition": {"datasource": {"id": datasource["id"]}},
    }

    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text

    # Duplicate task should be rejected as a conflict
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 409 == response.status_code, response.text
    assert "Task already scheduled on this type" in response.json["message"]

    # Test that we have only the one task
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.text
    print(response.json)
    assert 1 == len(response.json["items"])

    # Retrieve the task by id
    task_id = response.json["items"][0]["id"]
    response = client.get(
        f"/v1/tasks/{task_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text
    assert response.json.get("definition") is not None

    # When we delete the task, is it really gone?
    response = client.delete(
        f"/v1/tasks/{task_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.text

    response = client.get(
        f"/v1/tasks/{task_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 404 == response.status_code, response.text


def test_update_tasks(client, tc):
    # Create a task
    admin_session = tests.get_admin_session(app=client)

    datasource = create_datasource(client=client, session=admin_session)
    payload = {
        "type": "ingest_datasource",
        "schedule": "2 4 * * mon,fri",
        "definition": {"datasource": {"id": datasource["id"]}},
    }

    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text

    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.json
    assert 1 == len(response.json["items"])

    task_id = response.json["items"][0]["id"]

    response = client.get(
        f"/v1/tasks/{task_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 200 == response.status_code, response.json

    task = response.json

    task["schedule"] = "2 4 1 * wed"

    response = client.put(
        f"/v1/tasks/{task_id}",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(task),
    )
    assert 200 == response.status_code, response.json

    response = client.get(
        f"/v1/tasks/{task_id}",
        headers=tests.get_header(token=admin_session["token"]),
    )

    assert 200 == response.status_code, response.text
    assert "2 4 1 * wed" == response.json["schedule"]
