from typing import Optional

import nesis.api.core.models.objects as objects
import logging
from nesis.api.core import services
from nesis.api.core.document_loaders import validators

from nesis.api.core.models import DBSession
from nesis.api.core.models.entities import (
    Action,
    Datasource,
    DatasourceStatus,
    DatasourceType,
    RoleAction,
)

from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    is_valid_resource_name,
    has_valid_keys,
    PermissionException,
    ConflictException,
)

_LOG = logging.getLogger(__name__)


class DatasourceService(ServiceOperation):

    def __init__(
        self,
        config: dict,
        session_service=None,
    ):
        self._resource_type = objects.ResourceType.DATASOURCES
        self._session_service = session_service
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
        Create a datasource. Must have Datasource.CREATE permissions
        :param kwargs:
        :return:
        """
        datasource = kwargs["datasource"]

        session = DBSession()

        try:
            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.CREATE
            )

            session.expire_on_commit = False

            name = datasource.get("name")
            source_type: str = datasource.get("type")

            try:
                connection = validators.validate_datasource_connection(datasource)
            except ValueError as ve:
                raise ServiceException(ve)

            if not is_valid_resource_name(name):
                raise ServiceException(
                    "Invalid resource name. Must be least five in length and only include [a-z0-9_-]"
                )
            if not has_valid_keys(connection):
                raise ServiceException("Missing connection details")
            try:
                datasource_type = DatasourceType[source_type.upper()]
            except Exception:
                raise ServiceException("Invalid datasource type")

            entity = Datasource(
                name=name,
                connection=connection,
                status=DatasourceStatus.ONLINE,
                source_type=datasource_type,
            )

            session.add(entity)
            session.commit()
            session.refresh(entity)
            return entity
        except Exception as exc:
            session.rollback()
            error_str = str(exc).lower()

            if ("unique constraint" in error_str) and (
                "uq_datasource_name" in error_str
            ):
                # valid failure
                raise ConflictException("Datasource name already exists")
            else:
                raise
        finally:
            if session:
                session.close()

    def get(self, **kwargs):
        datasource_id = kwargs.get("datasource_id")

        session = DBSession()
        try:

            # Get datasources this user is authorized to access
            datasources = self._authorized_resources(
                session=session, action=Action.READ, token=kwargs.get("token")
            )

            session.expire_on_commit = False
            query = session.query(Datasource)
            if datasource_id:
                query = query.filter(Datasource.uuid == datasource_id)

            return [ds for ds in query.all() if ds.name in datasources]
        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()

    def _authorized_resources(self, token, session, action, resource=None):
        authorized_datasources: list[RoleAction] = services.authorized_resources(
            self._session_service,
            session=session,
            token=token,
            action=action,
            resource_type=objects.ResourceType.DATASOURCES,
        )
        datasources = {ds.resource for ds in authorized_datasources}
        if resource and resource not in datasources:
            raise PermissionException("Access to resource denied")

        return {ds.resource for ds in authorized_datasources}

    @staticmethod
    def get_datasources(source_type: str = None) -> list[Datasource]:
        session = DBSession()
        try:
            session.expire_on_commit = False
            query = session.query(Datasource)
            if source_type:
                query = query.filter(
                    Datasource.type == DatasourceType[source_type.upper()]
                )
            return list(query.all())
        finally:
            if session:
                session.close()

    def delete(self, **kwargs):

        datasource_id = kwargs["datasource_id"]

        session = DBSession()
        try:

            session.expire_on_commit = False
            datasource = (
                session.query(Datasource)
                .filter(Datasource.uuid == datasource_id)
                .first()
            )

            if datasource:
                self._authorized_resources(
                    session=session,
                    action=Action.DELETE,
                    token=kwargs.get("token"),
                    resource=datasource.name,
                )

                session.delete(datasource)
                session.commit()
        except Exception as e:
            self._LOG.exception(f"Error when deleting setting")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs):
        """
        Update the datasource. The payload only contains fields that we intend to update. Any missing fields will be
        ignored.
        :param kwargs: datasource the datasource object as a dict
        :param kwargs: id The datasource id
        :return:
        """
        datasource = kwargs["datasource"]
        datasource_id = kwargs["datasource_id"]

        session = DBSession()

        try:
            datasource_record: Datasource = (
                session.query(Datasource)
                .filter(Datasource.uuid == datasource_id)
                .first()
            )

            if datasource is None:
                raise ServiceException("Datasource not found")

            self._authorized_resources(
                session=session,
                action=Action.UPDATE,
                token=kwargs.get("token"),
                resource=datasource_record.name,
            )

            session.expire_on_commit = False

            source_type: str = datasource.get("type")
            if source_type is not None:
                try:
                    datasource_type = DatasourceType[source_type.upper()]
                    datasource_record.type = datasource_type
                except Exception:
                    raise ServiceException("Invalid datasource type")

            if datasource.get("connection"):
                try:
                    connection = validators.validate_datasource_connection(datasource)
                    datasource_record.connection = connection
                except ValueError as ve:
                    raise ServiceException(ve)

                if not has_valid_keys(connection):
                    raise ServiceException("Missing connection details")

            session.merge(datasource_record)
            session.commit()
            return datasource_record
        except Exception as e:
            session.rollback()
            self._LOG.exception(f"Error when creating setting")
            raise
        finally:
            if session:
                session.close()
