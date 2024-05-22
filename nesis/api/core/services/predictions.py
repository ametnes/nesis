import json
import uuid
from typing import Optional

import nesis.api.core.services as services
import nesis.api.core.util.common as common
import nesis.api.core.util.http as http
import logging
from nesis.api.core import util
from nesis.api.core.models import DBSession
from nesis.api.core.models.entities import (
    Prediction,
    Model,
    Module,
    Action,
    RoleAction,
)
from nesis.api.core.models.objects import ResourceType
from nesis.api.core.services.util import ServiceOperation, ServiceException

_LOG = logging.getLogger(__name__)


def _delete_prediction(session, **kwargs):
    prediction_id = kwargs.get("id")
    module = kwargs["module"]
    try:
        query = (
            session.query(Prediction)
            .filter(Prediction.module == module)
            .filter(Prediction.id == prediction_id)
            .first()
        )
        if query:
            session.delete(query)
            session.commit()
    except Exception as e:
        session.rollback()
        _LOG.exception(f"Error when getting validation data for module {module}")
        raise


def _get_prediction(session, **kwargs):
    module = kwargs["module"]
    model = kwargs.get("model")
    prediction_id = kwargs.get("id")

    try:
        session.expire_on_commit = False
        query = session.query(Prediction)
        if prediction_id:
            query = query.filter(Prediction.id == prediction_id)
        elif model:
            query = query.filter(Model.name == model).filter(
                Prediction.model == Model.id
            )
        elif module and model:
            query = query.filter(Prediction.module == module).filter(
                Prediction.model == model
            )
        elif module:
            query = query.filter(Prediction.module == module)
        else:
            raise ServiceException("Request must have mode, prediction_id or module")
        return query.all()
    except Exception as e:
        _LOG.exception(
            f"Error when fetching rules for module='{module}', model='{model}"
        )
        raise


class QandaPredictionService(ServiceOperation):

    def __init__(
        self,
        config: dict,
        client: Optional[http.HttpClient] = None,
        session_service=None,
    ) -> None:
        self._resource_type = ResourceType.PREDICTIONS
        self._session_service = session_service
        self._config = config
        self._client = client
        self._LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._LOG.info("Initializing service...")

        if self._client is None:
            self._client = http.HttpClient(config=self._config)

    def create(self, **kwargs) -> Prediction:
        payload = kwargs["payload"]
        save_results = payload.get("save") or False
        user_id = kwargs.get("user_id")

        session = DBSession()
        self.__authorized(
            session=session,
            token=kwargs.get("token"),
            action=Action.CREATE,
            user_id=user_id,
        )

        authorized_datasources: list[RoleAction] = services.authorized_resources(
            self._session_service,
            session=session,
            token=kwargs.get("token"),
            action=Action.READ,
            resource_type=ResourceType.DATASOURCES,
            user_id=user_id,
        )

        datasources = [ds.resource for ds in authorized_datasources]

        if len(datasources) == 0:
            raise ServiceException(
                "There are no datasources created or assigned to you"
            )

        request = {
            "messages": [{"role": "user", "content": payload["query"]}],
            "stream": False,
            "use_context": True,
            "include_sources": True,
        }

        if "*" not in datasources:
            request["context_filter"] = {"filters": {"datasource": datasources}}

        llm_config = self._config["rag"]
        response = self._client.post(
            url=f"{llm_config['endpoint']}/v1/chat/completions",
            headers=common.json_headers,
            payload=json.dumps(request),
        )
        prediction = Prediction(
            module=Module.qanda.name,
            model=None,
            input=payload["query"],
            data=json.loads(response),
        )
        if save_results:
            session = DBSession()
            try:
                session.expire_on_commit = False
                prediction.uid = str(uuid.uuid4())
                session.add(prediction)
                session.commit()
                session.refresh(prediction)
            except Exception:
                session.rollback()
                self._LOG.exception(f"Error when saving prediction {payload}")
                raise
            finally:
                if session:
                    session.close()
        return prediction

    def __authorized(self, session, token, action, user_id) -> dict:
        return services.authorized(
            session_service=self._session_service,
            session=session,
            token=token,
            action=action,
            resource_type=self._resource_type,
            user_id=user_id,
        )

    def delete(self, **kwargs):
        session = DBSession()
        try:
            self.__authorized(
                session=session, token=kwargs.get("token"), action=Action.DELETE
            )
            _delete_prediction(**kwargs)
        finally:
            if session:
                session.close()

    def get(self, **kwargs):
        session = DBSession()
        try:
            self.__authorized(
                session=session, token=kwargs.get("token"), action=Action.READ
            )
            return _get_prediction(**kwargs)
        finally:
            if session:
                session.close()

    def update(self, **kwargs):
        raise NotImplementedError("Invalid operation on datasource")
