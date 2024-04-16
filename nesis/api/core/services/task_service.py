import json
from typing import Optional, Dict, Any, Union, List
from croniter import croniter
import bcrypt
import memcache
from strgen import StringGenerator as SG

import logging
import nesis.api.core.services as services
from nesis.api.core.models import DBSession, objects
from nesis.api.core.models.objects import ResourceType, UserSession, TaskType
from nesis.api.core.models.entities import (
    User,
    Role,
    RoleAction,
    UserRole,
    Action,
    Datasource,
    Task,
)
from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    ConflictException,
    UnauthorizedAccess,
    PermissionException,
)

_LOG = logging.getLogger(__name__)


class TaskService(ServiceOperation):
    """
    This service operates on tasks. A task is any piece of work that the system runs in the background. It can be
    scheduled to run immediately or at a future date
    """

    def __init__(
        self,
        config: dict,
        session_service: ServiceOperation = None,
        datasource_service: ServiceOperation = None,
    ):
        self._resource_type = objects.ResourceType.TASKS
        self._session_service = session_service
        self._datasource_service = datasource_service
        self._config = config
        self._LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._LOG.info("Initializing service...")

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
    def _validate_schedule(schedule):
        if not croniter.is_valid(schedule):
            raise ValueError("Invalid schedule")

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
                self._validate_schedule(schedule)
            except ValueError as ve:
                raise ServiceException("Invalid schedule")

            entity = Task(
                schedule=schedule, task_type=task_type, definition=task_definition
            )

            session.add(entity)
            session.commit()
            session.refresh(entity)
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
            if schedule is not None:
                self._validate_schedule(schedule=schedule)
                task_record.schedule = schedule

            session.merge(task_record)
            session.commit()
            return task_record

        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()
