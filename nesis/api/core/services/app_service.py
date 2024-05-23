import base64
import logging
from typing import Dict, Any

import memcache
from strgen import StringGenerator as SG

import bcrypt

import nesis.api.core.services as services
from nesis.api.core.models import DBSession, objects
from nesis.api.core.models.entities import (
    RoleAction,
    Action,
    App,
    AppRole,
    Role,
)
from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    ConflictException,
    PermissionException,
    UnauthorizedAccess,
)
from nesis.api.core.util.http import HttpClient

_LOG = logging.getLogger(__name__)


class AppRoleService(ServiceOperation):
    """
    Manage app roles. This is a function of the app service. Permissions are part of the app function.
    Whatever a app is permitted to do on a app, they are permitted to do on the app role.
    For this reason, we don't check/test permissions in the app role service as it is called only in the app service.
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
            query = (
                session.query(AppRole)
                .filter(AppRole.role == Role.id)
                .filter(AppRole.app == App.id)
                .filter(App.uuid == app_id)
            )

            # Select a role id if supplied, otherwise delete all apps roles
            if uuid is not None:
                query = query.filter(Role.uuid == uuid)

            query.delete()
            session.commit()
        except Exception as e:
            self.__LOG.exception("Error when deleting app")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs) -> AppRole:
        raise NotImplementedError("Invalid operation on datasource")


class AppService(ServiceOperation):
    """
    This service operates on apps. A app is any piece of work that the system runs in the background. It can be
    scheduled to run immediately or at a future date
    """

    def __init__(
        self,
        config: dict,
        session_service: ServiceOperation,
    ):
        self._resource_type = objects.ResourceType.APPS
        self._session_service = session_service
        self._app_role_service = AppRoleService(
            config=config, session_service=session_service
        )
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

            secret = SG(r"[\l\d]{32}").render()
            secret_hash = bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt())

            entity = App(name=name, description=description, secret=secret_hash)

            session.add(entity)
            session.commit()

            # Attach any desired roles to the app
            for app_role in app.get("roles") or []:
                self._app_role_service.create(
                    **kwargs, app_id=entity.uuid, role={"id": app_role}
                )

            encoded_secret = base64.b64encode(
                f"{entity.uuid}:{secret}".encode("utf-8")
            ).decode("utf-8")
            entity.secret = encoded_secret

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

    @staticmethod
    def get_app(**kwargs) -> App:
        app_id = kwargs["app_id"]
        session = DBSession()
        try:
            return session.query(App).filter(App.uuid == app_id).first()
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

            app_roles = app.get("roles")
            if app_roles is not None:
                self._app_role_service.delete(**{**kwargs, "app_id": app_id})

                for app_role in app_roles:
                    try:
                        self._app_role_service.create(**kwargs, role={"id": app_role})
                    except ConflictException as ex:
                        self._LOG.info(ex)

            return app_record

        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()


class AppSessionService(ServiceOperation):
    """
    Manage user sessions
    """

    def __init__(self, config):
        self._config = config
        self._cache = memcache.Client(config["memcache"]["hosts"], debug=1)
        self._LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def get(self, **kwargs):
        token = kwargs.get("token")
        if token is None:
            raise UnauthorizedAccess("Token not supplied")

        key = self._cache_app_key(token)
        value = self._cache.get(key)

        if value is None:
            value = self.create(**kwargs)

        session_object = {"token": token, "app": value}

        return session_object

    def delete(self, **kwargs):
        raise NotImplementedError("Invalid operation on service")

    @staticmethod
    def _cache_app_key(key):
        return f"applications/{key}"

    def create(self, **kwargs) -> Dict[str, Any]:
        token = kwargs.get("token")
        if token is None:
            raise UnauthorizedAccess("Token not supplied")

        encoded_secret = base64.b64decode(token).decode("utf-8")
        encoded_secret_parts = encoded_secret.split(":")
        if len(encoded_secret_parts) != 2:
            raise UnauthorizedAccess("Invalid app token supplied")

        app: App = AppService.get_app(app_id=encoded_secret_parts[0])
        if app is None:
            raise UnauthorizedAccess("Invalid token")
        auth_secret = encoded_secret_parts[1].encode("utf-8")
        if not bcrypt.checkpw(auth_secret, app.secret):
            raise UnauthorizedAccess("Invalid app token supplied")
        value = app.to_dict()

        expiry = self._config["apps"]["session"]["expiry"]

        key = self._cache_app_key(token)

        self._cache.set(key=key, val=value, time=expiry)

        return value

    def update(self, **kwargs):
        raise NotImplementedError("Invalid operation on service")
