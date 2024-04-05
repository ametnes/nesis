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
)

from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    is_valid_resource_name,
    has_valid_keys,
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
        services.authorized(
            session_service=self._session_service,
            session=session,
            token=token,
            action=action,
            resource_type=self._resource_type,
        )

    def create(self, **kwargs):
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
        except Exception as e:
            session.rollback()
            self._LOG.exception(f"Error when creating setting")
            raise
        finally:
            if session:
                session.close()

    def get(self, **kwargs):
        datasource_id = kwargs.get("datasource_id")

        session = DBSession()
        try:

            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.READ
            )

            session.expire_on_commit = False
            query = session.query(Datasource)
            if datasource_id:
                query = query.filter(Datasource.uuid == datasource_id)

            return query.all()
        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()

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

            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.DELETE
            )

            session.expire_on_commit = False

            datasource = (
                session.query(Datasource)
                .filter(Datasource.uuid == datasource_id)
                .first()
            )

            if datasource:
                session.delete(datasource)
                session.commit()
        except Exception as e:
            self._LOG.exception(f"Error when deleting setting")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs):
        raise NotImplementedError("Invalid operation on datasource")
