import os
import unittest.mock as mock

import pytest
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
from nesis.api import tests
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine


@pytest.fixture
def session() -> None:
    return DBSession()


@pytest.fixture
def cache() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture(autouse=True)
def configure() -> None:
    os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1"

    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)
