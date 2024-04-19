import unittest as ut
import uuid

import pytest
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    JobEvent,
    EVENT_JOB_SUBMITTED,
)
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm.session import Session

import nesis.api.core.services as services
import nesis.api.core.util.dateutil as du
import nesis.api.tests as tests
from nesis.api.core.models import initialize_engine, DBSession
from nesis.api.core.models.entities import Datasource, Task, DatasourceStatus
from nesis.api.core.models.objects import TaskType, TaskStatus
from nesis.api.core.services.util import ServiceException
from nesis.api.core.util import http
from nesis.api.tests.core.services import (
    create_user_session,
)


@pytest.fixture
def tc():
    return ut.TestCase()


@pytest.fixture(autouse=True)
def setup():

    pytest.config = tests.config
    initialize_engine(tests.config)
    session: Session = DBSession()
    tests.clear_database(session)

    services.init_services(
        config=tests.config, http_client=http.HttpClient(config=tests.config)
    )
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


def test_task_cron_scheduler(tc):
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
    task.enabled = False
    task_dict = task.to_dict()
    updated_task = services.task_service.update(
        token=admin_user.token, task_id=task_dict["id"], task=task_dict
    )
    job_list = services.task_service._scheduler.get_jobs()
    assert 1 == len(job_list)
    tc.assertListEqual(
        job_list[0].trigger.fields, CronTrigger.from_crontab("2 4 * * mon,sun").fields
    )

    # TODO - Worth testing that the job was paused but the apscheduler doesn't seem to have an API for that


def test_task_date_scheduler(tc):
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

    # Create a task and ensure that it is listed in the scheduler
    job_list = services.task_service._scheduler.get_jobs()
    assert 0 == len(job_list)

    # A scheduled in the past triggers an error
    with pytest.raises(ServiceException) as ex_info:
        create_task(
            token=admin_user.token,
            datasource=datasource,
            schedule=du.dt.datetime.strftime(
                du.now() - du.dt.timedelta(days=2), du.YYYY_MM_DD_HH_MM_SS
            ),
        )
        assert "Schedule date has to be in the future" in str(ex_info)

    schedule = du.now() + du.dt.timedelta(seconds=+5)
    task: Task = create_task(
        token=admin_user.token,
        datasource=datasource,
        schedule=du.dt.datetime.strftime(schedule, du.YYYY_MM_DD_HH_MM_SS),
    )
    assert task.id is not None

    # Ensure the task job is configured as we expect
    job_list = services.task_service._scheduler.get_jobs()
    assert 1 == len(job_list)
    assert du.dt.datetime.strftime(
        schedule, du.YYYY_MM_DD_HH_MM_SS
    ) == du.dt.datetime.strftime(job_list[0].trigger.run_date, du.YYYY_MM_DD_HH_MM_SS)


@pytest.mark.parametrize(
    "event_code, task_expected, datasource_expected",
    [
        (EVENT_JOB_SUBMITTED, TaskStatus.RUNNING, DatasourceStatus.INGESTING),
        (EVENT_JOB_EXECUTED, TaskStatus.COMPLETED, DatasourceStatus.ONLINE),
        (EVENT_JOB_ERROR, TaskStatus.ERROR, DatasourceStatus.ONLINE),
    ],
)
def test_task_listener(tc, event_code, task_expected, datasource_expected):
    """
    Test the task listener updates the task and datasource during ingestion.
    """

    admin_user = create_user_session(
        service=services.user_session_service,
        email=tests.admin_email,
        password=tests.admin_password,
    )
    datasource: Datasource = create_datasource(token=admin_user.token)

    task = Task(
        task_type=TaskType.INGEST_DATASOURCE,
        schedule=str(du.now()),
        definition={},
        parent_id=datasource.uuid,
    )
    session: Session = DBSession()
    session.add(task)
    session.commit()

    # Submitted event
    submit_event: JobEvent = JobEvent(code=event_code, job_id=task.uuid, jobstore=None)

    services.task_service._scheduler_listener(event=submit_event)

    task = session.query(Task).filter(Task.uuid == task.uuid).first()
    datasource = (
        session.query(Datasource).filter(Datasource.uuid == task.parent_id).first()
    )
    assert task.status == task_expected
    assert datasource.status == datasource_expected


def test_task_listener_invalid_job(tc):

    # Fail with ValueError if job_id is invalid
    submit_event: JobEvent = JobEvent(
        code=EVENT_JOB_EXECUTED, job_id=str(uuid.uuid4()), jobstore=None
    )

    with pytest.raises(ValueError) as ex_info:
        services.task_service._scheduler_listener(event=submit_event)
        assert "not found" in str(ex_info)
