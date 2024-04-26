import os
import pytest
import unittest.mock as mock

from sqlalchemy.orm.session import Session

from nesis.api import tests
from nesis.api.core.models import DBSession
from nesis.api.core.models import initialize_engine
import nesis.api.core.services as services


@pytest.fixture
def session() -> None:
    return DBSession()


@pytest.fixture
def cache() -> mock.MagicMock:
    return mock.MagicMock()


@pytest.fixture(autouse=True)
def configure() -> None:
    os.environ["OPENAI_API_BASE"] = "http://localhost:8080/v1"

    # self.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    os.environ["OPENAI_API_KEY"] = "some.api.key"

    services.init_services(tests.config)
