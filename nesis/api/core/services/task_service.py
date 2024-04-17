import pytz
import logging
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, Any, List, Optional

import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger, BaseTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    JobEvent,
    JobSubmissionEvent,
    JobExecutionEvent,
    EVENT_JOB_SUBMITTED,
)

import nesis.api.core.services as services
from nesis.api.core.models import DBSession, objects
from nesis.api.core.models.entities import (
    RoleAction,
    Action,
    Datasource,
    Task,
)
from nesis.api.core.models.objects import TaskType, TaskStatus
from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    ConflictException,
    PermissionException,
)
from nesis.api.core.tasks.document_management import ingest_datasource
from nesis.api.core.util.http import HttpClient
import nesis.api.core.util.dateutil as du


_LOG = logging.getLogger(__name__)


class TaskService(ServiceOperation):
    """
    This service operates on tasks. A task is any piece of work that the system runs in the background. It can be
    scheduled to run immediately or at a future date
    """

    def __init__(
        self,
        config: dict,
        http_client: HttpClient,
        session_service: ServiceOperation = None,
        datasource_service: ServiceOperation = None,
    ):
        self._resource_type = objects.ResourceType.TASKS
        self._session_service = session_service
        self._datasource_service = datasource_service
        self._http_client = http_client
        self._config = config
        self._LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._LOG.info("Initializing service...")

        self._setup_scheduler()

    def _setup_scheduler(self):
        job_stores = {
            "default": SQLAlchemyJobStore(
                url=self._config["tasks"]["job"]["stores"]["url"], tablename="task_job"
            )
        }
        executors = {
            "default": ThreadPoolExecutor(
                self._config["tasks"]["executors"]["default_size"]
            ),
            "processpool": ProcessPoolExecutor(
                self._config["tasks"]["executors"]["pool_size"]
            ),
        }
        self._scheduler = BackgroundScheduler(
            jobstores=job_stores,
            executors=executors,
            job_defaults=self._config["tasks"]["job"]["defaults"],
            timezone=pytz.timezone(self._config["tasks"]["timezone"]),
        )
        try:
            self._scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self._scheduler.shutdown(wait=False)
            _LOG.info(f"Terminating scheduler process")

    def _authorized(self, session, token, action):
        """
        Check if request is authenticated
        :param session:
        :param token:
        :param action:
        :return:
        """
        services.authorized(
            session_service=self._session_service,
            session=session,
            token=token,
            action=action,
            resource_type=self._resource_type,
        )

    def _validate_definition(
        self, token, task_type: TaskType, definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates the task definition. For now, tasks are only available on Datasources but this can be easily.
        Returns a modified task definition with only the valid fields
        """
        if definition is None:
            raise ValueError("Task definition must be supplied")
        match task_type:
            case TaskType.INGEST_DATASOURCE:
                datasource = definition.get("datasource")
                if datasource is None:
                    raise ValueError("Task definition for datasource missing")
                datasource_records: List[Datasource] = self._datasource_service.get(
                    token=token, datasource_id=datasource.get("id")
                )
                if len(datasource_records) == 0:
                    raise ValueError("Invalid datasource supplied")
                return {"datasource": {"id": datasource["id"]}}
            case _:
                raise ValueError("Invalid task type")

    @staticmethod
    def _validate_schedule(schedule) -> BaseTrigger:
        try:
            # While apscheduler can make the conversion, we do it here to have full control of error behaviour
            schedule_date = du.strptime(schedule)
            trigger = DateTrigger(run_date=schedule_date)
        except ValueError:
            schedule_date: Optional[du.dt.datetime] = None
            trigger: Optional[DateTrigger] = None

        if all([schedule_date, trigger]):
            if schedule_date < du.now():
                raise ValueError("Schedule date has to be in the future")
            else:
                return trigger

        return CronTrigger.from_crontab(schedule)

    def create(self, **kwargs):
        """
        Create a task. Must have Task.CREATE permissions
        :param kwargs:
        :return:
        """
        task = kwargs["task"]

        session = DBSession()

        try:
            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.CREATE
            )

            session.expire_on_commit = False

            schedule: str = task.get("schedule")
            task_type_str: str = task.get("type")
            definition: Dict[str, Any] = task.get("definition")

            try:
                task_type = TaskType[task_type_str.upper()]
            except Exception:
                raise ServiceException("Invalid task type")

            try:
                task_definition = self._validate_definition(
                    token=kwargs.get("token"),
                    definition=definition,
                    task_type=task_type,
                )
            except ValueError as ve:
                raise ServiceException(ve)

            try:
                trigger = self._validate_schedule(schedule)
            except ValueError as e:
                raise ServiceException(e)

            entity = Task(
                schedule=schedule, task_type=task_type, definition=task_definition
            )

            session.add(entity)
            session.commit()
            session.refresh(entity)

            self._scheduler.add_job(
                func=ingest_datasource,
                trigger=trigger,
                id=entity.uuid,
                kwargs={"params": task_definition, "config": self._config},
            )
            self._scheduler.add_listener(
                self._setup_scheduler,
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_SUBMITTED,
            )

            return entity
        except Exception as exc:
            session.rollback()
            error_str = str(exc).lower()

            if ("unique constraint" in error_str) and (
                "uq_task_type_schedule" in error_str
            ):
                # valid failure
                raise ConflictException("Task already scheduled on this type")
            else:
                raise
        finally:
            if session:
                session.close()

    @staticmethod
    def _scheduler_listener(event: JobEvent) -> None:
        session = DBSession()
        job_id = event.job_id

        if hasattr(event, "exception"):
            if event.exception is not None:
                _LOG.warning(f"Task {job_id} failed with error {event.exception}")
                return

        task: Task = session.query(Task).filter(Task.uuid == job_id).first()
        if task is None:
            _LOG.warning(f"Task {job_id} not found. May have been deleted")
            return

        match event.code:
            case apscheduler.events.EVENT_JOB_SUBMITTED:
                task.status = TaskStatus.RUNNING
            case apscheduler.events.EVENT_JOB_EXECUTED:
                task.status = TaskStatus.IDLE

        session.merge(task)
        try:
            session.commit()
        except:
            _LOG.warning(f"Error when saving task {job_id} status", exc_info=True)

    def get(self, **kwargs):
        task_id = kwargs.get("task_id")

        session = DBSession()
        try:

            # Get tasks this user is authorized to access
            tasks = self._authorized_resources(
                session=session, action=Action.READ, token=kwargs.get("token")
            )

            session.expire_on_commit = False
            query = session.query(Task).filter(Task.uuid.in_(tasks))
            if task_id:
                query = query.filter(Task.uuid == task_id)

            return query.all()
        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()

    def _authorized_resources(self, token, session, action, resource=None):
        authorized_tasks: list[RoleAction] = services.authorized_resources(
            self._session_service,
            session=session,
            token=token,
            action=action,
            resource_type=objects.ResourceType.TASKS,
        )
        tasks = {task.resource for task in authorized_tasks}
        if resource and resource not in tasks:
            raise PermissionException("Access to resource denied")

        return {ds.resource for ds in authorized_tasks}

    def delete(self, **kwargs):

        task_id = kwargs["task_id"]

        session = DBSession()
        try:

            session.expire_on_commit = False
            task = session.query(Task).filter(Task.uuid == task_id).first()

            if task:
                self._authorized_resources(
                    session=session,
                    action=Action.DELETE,
                    token=kwargs.get("token"),
                    resource=task.uuid,
                )

                session.delete(task)
                session.commit()

                self._scheduler.remove_job(job_id=task.uuid)

        except Exception as e:
            self._LOG.exception(f"Error when deleting setting")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs):
        task_id = kwargs["task_id"]
        task = kwargs["task"]

        session = DBSession()
        try:

            # Get tasks this user is authorized to access
            self._authorized_resources(
                session=session,
                action=Action.UPDATE,
                token=kwargs.get("token"),
                resource=task_id,
            )

            session.expire_on_commit = False

            task_record: Task = session.query(Task).filter(Task.uuid == task_id).first()

            enabled = task.get("enabled")
            if enabled is not None and isinstance(enabled, bool):
                task_record.enabled = enabled

            schedule = task.get("schedule")
            cron_job = None
            if schedule is not None:
                try:
                    cron_job = self._validate_schedule(schedule)
                except ValueError as ve:
                    raise ServiceException("Invalid schedule/cron expression")

                task_record.schedule = schedule

            session.merge(task_record)
            session.commit()

            # Update job only after updating the record
            if cron_job is not None:
                self._scheduler.reschedule_job(
                    job_id=task_record.uuid, trigger=cron_job
                )

            # If task is disabled, we pause the job
            if not task_record.enabled:
                self._scheduler.pause_job(task_record.uuid)
            else:
                self._scheduler.resume_job(task_record.uuid)

            return task_record

        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()
