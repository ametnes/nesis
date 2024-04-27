import json

import yaml

import unittest as ut
import unittest.mock as mock

import pytest

from sqlalchemy.orm.session import Session
from nesis.api.core.controllers import app as cloud_app
import nesis.api.tests as tests
import nesis.api.core.services as services
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

    services.init_services(config=tests.config, http_client=http_client)
    return cloud_app.test_client()


def create_datasource(client, session):
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

    response = client.post(
        f"/v1/datasources",
        headers=tests.get_header(token=session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.json


def test_predictions(client, http_client, tc):
    """
    Test the prediction happy path
    """
    admin_session = tests.get_admin_session(app=client)

    payload = {"query": "Summarise the office agreement"}
    engine_response = {
        "choices": [
            {
                "delta": None,
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "The Office Agreement is a document that outlines the terms and conditions for the use "
                    "of Office software, which is a suite of office productivity tools. It typically includes "
                    "information on licensing, usage rights, restrictions, and support services provided by Office.",
                    "role": "assistant",
                },
                "sources": [],
            }
        ],
        "created": 1711927022,
        "id": "543d0464-85e4-41ab-b136-b8023e3cc4d8",
        "model": "rag",
        "object": "completion",
    }
    output = {
        "create_date": "2024-03-31 23:17:02",
        "data": engine_response,
        "input": "Summarise the office agreement",
        "module": "qanda",
    }

    # Test authentication to endpoint
    http_client.post.side_effect = [json.dumps(engine_response)] * 5
    response = client.post(
        f"/v1/modules/qanda/predictions",
        headers=tests.get_header(),
        data=json.dumps(payload),
    )
    assert 401 == response.status_code, response.json

    # We need to have set up a datasource first
    create_datasource(client=client, session=admin_session)
    # Test prediction without saving
    response = client.post(
        f"/v1/modules/qanda/predictions",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.json
    prediction = response.json
    assert prediction.get("id") is None
    tc.assertDictEqual(prediction["data"], output["data"])

    # Assert that the payload has use_context enabled
    _, kwargs_http_client_post = http_client.post.call_args_list[0]
    kwargs_http_client_post_payload = json.loads(kwargs_http_client_post["payload"])
    tc.assertDictEqual(
        kwargs_http_client_post_payload,
        {
            "context_filter": {"filters": {"datasource": ["finance6"]}},
            "include_sources": True,
            "messages": [{"content": "Summarise the office agreement", "role": "user"}],
            "stream": False,
            "use_context": True,
        },
    )

    # Test prediction with saving
    response = client.post(
        f"/v1/modules/qanda/predictions",
        headers=tests.get_header(token=admin_session["token"]),
        data=json.dumps({**payload, "save": True}),
    )
    assert 200 == response.status_code, response.json
    prediction = response.json["data"]
    assert prediction.get("id") is not None
    tc.assertDictEqual(response.json["data"], output["data"])
