import json
import uuid

from apscheduler.triggers.cron import CronTrigger

import unittest as ut
import unittest.mock as mock

import pytest

from sqlalchemy.orm.session import Session
import nesis.api.tests as tests
import nesis.api.core.services as services
from nesis.api.core.models import initialize_engine, DBSession
from nesis.api.core.models.entities import Datasource, Task
from nesis.api.core.services import PermissionException
from nesis.api.tests.core.services import (
    create_user_session,
    create_role,
    assign_role,
)


@pytest.fixture
def http_client():
    return mock.MagicMock()


@pytest.fixture
def tc():
    return ut.TestCase()


@pytest.fixture(autouse=True)
def setup(http_client):

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    services.init_services(config=tests.config, http_client=http_client)
    services.task_service._scheduler.remove_all_jobs()


def create_datasource(token: str) -> Datasource:
    payload = {
        "type": "minio",
        "name": str(uuid.uuid4()),
        "connection": {
            "user": "caikuodda",
            "password": "password",
            "host": "localhost",
            "port": "5432",
            "database": "initdb",
        },
    }

    return services.datasource_service.create(datasource=payload, token=token)


def create_task(token: str, datasource: Datasource, schedule: str) -> Datasource:
    payload = {
        "type": "ingest_datasource",
        "name": str(uuid.uuid4()),
        "schedule": schedule,
        "definition": {
            "datasource": {"id": datasource.uuid},
        },
    }

    return services.task_service.create(task=payload, token=token)


def test_task_scheduler(http_client, tc):
    """
    Test the task happy path
    """

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )
    datasource: Datasource = create_datasource(token=admin_user.token)
    assert datasource.id is not None
    assert datasource.uuid is not None

    # User can now create a datasource
    datasource: Datasource = create_datasource(token=admin_user.token)
    assert datasource.id is not None

    # Create a task and ensure that it is listed in the scheduler
    job_list = services.task_service._scheduler.get_jobs()
    assert 0 == len(job_list)

    task: Task = create_task(
        token=admin_user.token, datasource=datasource, schedule="2 4 * * mon,fri"
    )
    assert task.id is not None

    # Ensure the task job is configured as we expect
    job_list = services.task_service._scheduler.get_jobs()
    assert 1 == len(job_list)
    tc.assertListEqual(
        job_list[0].trigger.fields, CronTrigger.from_crontab("2 4 * * mon,fri").fields
    )

    # Update the task and ensure that the job is updated to
    task.schedule = "2 4 * * mon,sun"
    task_dict = task.to_dict()
    updated_task = services.task_service.update(
        token=admin_user.token, task_id=task_dict["id"], task=task_dict
    )
    job_list = services.task_service._scheduler.get_jobs()
    assert 1 == len(job_list)
    tc.assertListEqual(
        job_list[0].trigger.fields, CronTrigger.from_crontab("2 4 * * mon,sun").fields
    )
