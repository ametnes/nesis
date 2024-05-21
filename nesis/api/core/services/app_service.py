import logging
from typing import Dict, Any, List, Optional

import apscheduler
import pytz
from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_EXECUTED,
    JobEvent,
    EVENT_JOB_SUBMITTED,
    EVENT_JOB_ADDED,
)
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

import nesis.api.core.services as services
import nesis.api.core.util.dateutil as du
from nesis.api.core.models import DBSession, objects
from nesis.api.core.models.entities import (
    RoleAction,
    Action,
    Datasource,
    Task,
    DatasourceStatus,
    App,
    AppRole,
    Role,
)
from nesis.api.core.models.objects import TaskType, TaskStatus
from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    ConflictException,
    PermissionException,
)
from nesis.api.core.services.util import validate_schedule
from nesis.api.core.apps.document_management import ingest_datasource
from nesis.api.core.util.http import HttpClient

_LOG = logging.getLogger(__name__)


class AppRoleService(ServiceOperation):
    """
    Manage user roles. This is a function of the user service. Permissions are part of the user function.
    Whatever a user is permitted to do on a user, they are permitted to do on the user role.
    For this reason, we don't check/test permissions in the user role service as it is called only in the user service.
    """

    def __init__(self, config: dict, session_service: ServiceOperation):
        self.__resource_type = objects.ResourceType.APPS
        self.__config = config
        self.__session_service = session_service
        self.__LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self.__LOG.info("Initializing service...")

    def create(self, **kwargs) -> AppRole:
        app_id: str = kwargs["app_id"]
        app_role: dict = kwargs["role"]

        session = DBSession()
        try:
            session.expire_on_commit = False

            role: Role = session.query(Role).filter(Role.uuid == app_role["id"]).first()
            app: App = session.query(App).filter(App.uuid == app_id).first()

            if not all([role, app]):
                raise ServiceException("Invalid role or app")

            app_role: AppRole = AppRole(app=app, role=role)

            session.add(app_role)
            session.commit()
            session.refresh(app_role)

            return app_role
        except Exception as e:
            session.rollback()
            self.__LOG.exception(f"Error when creating role")

            error_str = str(e)

            if ("unique constraint" in error_str) and (
                "uq_app_role_app_role" in error_str
            ):
                # valid failure
                raise ConflictException("Role already attached to app")
            else:
                raise
        finally:
            if session:
                session.close()

    def get(self, **kwargs) -> list[AppRole]:
        app_id = kwargs.get("app_id")
        session = DBSession()
        try:
            session.expire_on_commit = False

            return (
                session.query(Role)
                .filter(Role.id == AppRole.role)
                .filter(AppRole.user == App.id)
                .filter(App.uuid == app_id)
                .all()
            )
        except:
            self.__LOG.exception("Error when fetching users")
            raise
        finally:
            if session:
                session.close()

    def delete(self, **kwargs):
        uuid = kwargs.get("id")
        app_id = kwargs["app_id"]
        session = DBSession()
        try:
            session.expire_on_commit = False

            if uuid is None:
                query = (
                    session.query(AppRole)
                    .filter(AppRole.role == Role.id)
                    .filter(AppRole.user == App.id)
                    .filter(App.uuid == app_id)
                )
            else:
                query = (
                    session.query(AppRole)
                    .filter(AppRole.role == Role.id)
                    .filter(AppRole.user == App.id)
                    .filter(Role.uuid == uuid)
                    .filter(App.uuid == app_id)
                )
            query.delete()
            session.commit()
        except Exception as e:
            self.__LOG.exception("Error when deleting app")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs) -> AppRole:
        role_uuid = kwargs["id"]
        role: dict = kwargs["role"]

        session = DBSession()
        try:
            session.expire_on_commit = False

            role_record = session.query(Role).filter(Role.uuid == role_uuid)
            session.query(AppRole).filter(Role.uuid == role_uuid).filter(
                AppRole.role == Role.id
            ).delete()

            role_actions: Optional[dict] = role.get("policy")

            for action in role_actions:
                action_resource: Optional[str] = action.get("resource")
                action_actions: Optional[set[str]] = action.get("policy")
                action_resources: Optional[set[str]] = action.get("resources") or set()

                if not any([action_resource, action_resources]):
                    raise ServiceException("resource or resources must be supplied")

                if action_resource:
                    action_resources.add(action_resource)

                for action_resource in action_resources:
                    for action_actions_action in action_actions:
                        role_action = RoleAction(
                            action=action_actions_action,
                            role=role_record.id,
                            resource=action_resource,
                            resource_type=objects.ResourceType.APPS,
                        )
                        session.add(role_action)

            session.commit()

            return role_record

        except Exception as e:
            session.rollback()
            self.__LOG.exception(f"Error when updating user")
            raise
        finally:
            if session:
                session.close()


class AppService(ServiceOperation):
    """
    This service operates on apps. A app is any piece of work that the system runs in the background. It can be
    scheduled to run immediately or at a future date
    """

    def __init__(
        self,
        config: dict,
        http_client: HttpClient,
        session_service: ServiceOperation,
    ):
        self._resource_type = objects.ResourceType.APPS
        self._session_service = session_service
        self._app_role_service = AppRoleService(
            config=config, session_service=session_service
        )
        self._http_client = http_client
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

    def create(self, **kwargs):
        """
        Create an app. Must have App.CREATE permissions
        :param kwargs:
        :return:
        """
        app = kwargs["app"]

        session = DBSession()

        try:
            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.CREATE
            )

            session.expire_on_commit = False

            name: str = app.get("name")
            description: str = app.get("description")

            entity = App(
                name=name,
                description=description,
            )

            session.add(entity)
            session.commit()
            session.refresh(entity)

            for app_role in app.get("roles") or []:
                self._app_role_service.create(
                    **kwargs, user_id=entity.uuid, role={"id": app_role}
                )

            return entity
        except Exception as exc:
            session.rollback()
            error_str = str(exc).lower()

            if ("unique constraint" in error_str) and ("uq_app_name" in error_str):
                # valid failure
                raise ConflictException("Application already exists")
            else:
                raise
        finally:
            if session:
                session.close()

    def get(self, **kwargs):
        app_id = kwargs.get("app_id")

        session = DBSession()
        try:

            apps = self._authorized_resources(
                session=session, action=Action.READ, token=kwargs.get("token")
            )

            session.expire_on_commit = False
            query = session.query(App).filter(App.uuid.in_(apps))
            if app_id:
                query = query.filter(App.uuid == app_id)
            return query.all()
        except Exception as e:
            self._LOG.exception(f"Error when fetching apps")
            raise
        finally:
            if session:
                session.close()

    def _authorized_resources(self, token, session, action, resource=None):
        authorized_apps: list[RoleAction] = services.authorized_resources(
            self._session_service,
            session=session,
            token=token,
            action=action,
            resource_type=objects.ResourceType.APPS,
        )
        apps = {app.resource for app in authorized_apps}
        if resource and resource not in apps:
            raise PermissionException("Access to resource denied")

        return {ds.resource for ds in authorized_apps}

    def delete(self, **kwargs):

        app_id = kwargs["app_id"]

        session = DBSession()
        try:

            session.expire_on_commit = False
            app = session.query(App).filter(App.uuid == app_id).first()

            if app:
                self._authorized_resources(
                    session=session,
                    action=Action.DELETE,
                    token=kwargs.get("token"),
                    resource=app.uuid,
                )

                session.delete(app)
                session.commit()

        except Exception:
            session.rollback()
            self._LOG.exception(f"Error when deleting setting")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs):
        app_id = kwargs["app_id"]
        app = kwargs["app"]

        session = DBSession()
        try:

            # Get apps this user is authorized to access
            self._authorized_resources(
                session=session,
                action=Action.UPDATE,
                token=kwargs.get("token"),
                resource=app_id,
            )

            session.expire_on_commit = False

            app_record: App = session.query(App).filter(App.uuid == app_id).first()

            enabled = app.get("enabled")
            if enabled is not None and isinstance(enabled, bool):
                app_record.enabled = enabled

            name = app.get("name")
            if name is not None:
                app_record.name = name

            description = app.get("description")
            if description is not None:
                app_record.description = description

            session.merge(app_record)
            session.commit()

            return app_record

        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()
