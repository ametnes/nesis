import json
import unittest as ut
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


def create_task(client, datasource, session):
    payload = {
        "type": "ingest_datasource",
        "schedule": "2 4 * * mon,fri",
        "definition": {"datasource": {"id": datasource["id"]}},
    }

    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text
    return response.json


def test_unauthorized(client, tc):

    admin_session = tests.get_admin_session(app=client)
    datasource = create_datasource(client=client, session=admin_session)
    task = create_task(client=client, session=admin_session, datasource=datasource)

    role_payload = {
        "name": f"task-manager-{uuid.uuid4()}",
        "policy": {
            "items": [
                {"action": "read", "resource": f"datasources/{datasource['name']}"},
                # {"action": "create", "resource": f"tasks/*"},
            ]
        },
    }
    role = tests.create_role(client=client, session=admin_session, role=role_payload)

    user_session = tests.get_user_session(
        client=client, session=admin_session, roles=[role["id"]]
    )
    payload = {
        "type": "ingest_datasource",
        "schedule": "2 4 * * mon,fri",
        "definition": {"datasource": {"id": datasource["id"]}},
    }

    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(payload),
    )
    assert 403 == response.status_code, response.text

    response = client.put(
        f"/v1/tasks/{task['id']}",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(payload),
    )
    assert 403 == response.status_code, response.text

    # Test that we cannot read any tasks
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=user_session["token"])
    )
    assert 200 == response.status_code, response.text
    assert len(response.json["items"]) == 0

    # Test that we cannot delete the task
    response = client.delete(
        f"/v1/tasks/{task['id']}",
        headers=tests.get_header(token=user_session["token"]),
    )
    assert 403 == response.status_code, response.text

    # Make sure the task was not deleted. We check as the adminsitrator
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=admin_session["token"])
    )
    assert 200 == response.status_code, response.text
    assert len(response.json["items"]) == 1


def test_authorized(client, tc):

    admin_session = tests.get_admin_session(app=client)
    datasource = create_datasource(client=client, session=admin_session)
    # task = create_task(client=client, session=admin_session, datasource=datasource)

    role_payload = {
        "name": f"task-manager-{uuid.uuid4()}",
        "policy": {
            "items": [
                {"action": "read", "resource": f"datasources/{datasource['name']}"},
                {"action": "create", "resource": f"tasks/*"},
                {"action": "delete", "resource": f"tasks/*"},
                {"action": "read", "resource": f"tasks/*"},
                {"action": "update", "resource": f"tasks/*"},
            ]
        },
    }
    role = tests.create_role(client=client, session=admin_session, role=role_payload)

    user_session = tests.get_user_session(
        client=client, session=admin_session, roles=[role["id"]]
    )
    payload = {
        "type": "ingest_datasource",
        "schedule": "2 4 * * mon,fri",
        "definition": {"datasource": {"id": datasource["id"]}},
    }

    # The user can create a task
    response = client.post(
        f"/v1/tasks",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text
    task = response.json

    # The user can update the task
    response = client.put(
        f"/v1/tasks/{task['id']}",
        headers=tests.get_header(token=user_session["token"]),
        data=json.dumps({**payload, "schedule": "0 0 * * 5#3,L5"}),
    )
    assert 200 == response.status_code, response.text
    task = response.json

    # Test that user can read any tasks
    response = client.get(
        "/v1/tasks", headers=tests.get_header(token=user_session["token"])
    )
    assert 200 == response.status_code, response.text
    assert len(response.json["items"]) == 1

    # Test that user can delete the task
    response = client.delete(
        f"/v1/tasks/{task['id']}",
        headers=tests.get_header(token=user_session["token"]),
    )
    assert 200 == response.status_code, response.text

    # Confirm that the task is gone
    response = client.get(
        f"/v1/tasks/{task['id']}",
        headers=tests.get_header(token=admin_session["token"]),
    )
    assert 404 == response.status_code, response.text
