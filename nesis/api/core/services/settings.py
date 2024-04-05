from typing import List
import logging
from nesis.api.core import services
from nesis.api.core.models import DBSession
from nesis.api.core.models.entities import Setting, Action
from nesis.api.core.models.objects import ResourceType

from nesis.api.core.services.util import ServiceOperation

_LOG = logging.getLogger(__name__)


class SettingsService(ServiceOperation):
    def update(self, **kwargs):
        raise NotImplementedError("Invalid operation on datasource")

    def __init__(self, config: dict, session_service) -> None:
        self._resource_type = ResourceType.SETTINGS
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
        setting = kwargs["setting"]
        module = setting["module"]

        session = DBSession()

        try:
            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.CREATE
            )

            session.expire_on_commit = False

            name = setting.get("name")
            attributes = setting.get("attributes")

            entity = Setting(name=name, attributes=attributes, module=module)

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
        setting_id = kwargs.get("setting_id")
        module = kwargs["module"]

        session = DBSession()
        try:

            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.READ
            )

            session.expire_on_commit = False
            query = session.query(Setting).filter(Setting.module == module)
            if setting_id:
                query = query.filter(Setting.id == setting_id)

            return query.all()
        except Exception as e:
            self._LOG.exception(f"Error when fetching settings")
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def get_settings(module) -> List[Setting]:
        session = DBSession()
        try:
            session.expire_on_commit = False
            return list(session.query(Setting).filter(Setting.module == module))
        finally:
            if session:
                session.close()

    def delete(self, **kwargs):

        setting_id = kwargs["setting_id"]
        module = kwargs["module"]

        session = DBSession()
        try:

            self._authorized(
                session=session, token=kwargs.get("token"), action=Action.DELETE
            )

            session.expire_on_commit = False

            rule = (
                session.query(Setting)
                .filter(Setting.id == setting_id)
                .filter(Setting.module == module)
                .first()
            )

            if rule:
                session.delete(rule)
                session.commit()
        except Exception as e:
            self._LOG.exception(f"Error when deleting setting")
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def create_or_update(setting):
        setting_id = setting.get("setting_id")

        if setting_id is not None:
            module = setting.get("module")

            session = DBSession()
            try:
                session.expire_on_commit = False

                db_setting = (
                    session.query(Setting)
                    .filter(Setting.id == setting_id)
                    .filter(Setting.module == module)
                    .first()
                )

                if db_setting:
                    db_setting.attributes = setting["attributes"]
                    session.commit()
                    return db_setting
            except Exception as e:
                raise
            finally:
                if session:
                    session.close()
        else:
            settings_service = SettingsService(setting)
            return settings_service.create(setting=setting)
