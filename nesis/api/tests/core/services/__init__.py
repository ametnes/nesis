from typing import Tuple

from nesis.api.core.models.entities import UserRole, Role, Datasource, Prediction
from nesis.api.core.services import (
    UserService,
    UserSessionService,
    RoleService,
    UserRoleService,
    AppService,
    DatasourceService,
    QandaPredictionService,
)


def create_user_session(service: UserSessionService, email, password):
    admin_data = {
        "password": password,
        "email": email,
    }
    return service.create(session=admin_data)


def create_user(service: UserService, token, email, password, role_ids=None):
    data = {
        "name": email,
        "password": password,
        "email": email,
        "roles": role_ids,
    }
    return service.create(user=data, token=token)


def create_role(
    service: RoleService,
    token: str,
    role: dict,
) -> Role:
    role_record = service.create(role=role, token=token)
    return role_record


def assign_role_to_user(service: UserService, token: str, role: dict, user_id: str):
    service.update(token=token, user_id=user_id, user={"roles": [role["id"]]})


def assign_role_to_app(service: AppService, token: str, role: dict, app_id: str):
    service.update(token=token, app_id=app_id, app={"roles": [role["id"]]})


def create_datasource(
    service: DatasourceService, token: str, name: str = None
) -> Datasource:
    payload = {
        "type": "minio",
        "name": name or "finance6",
        "connection": {
            "user": "caikuodda",
            "password": "some.password",
            "endpoint": "localhost",
            "dataobjects": "initdb",
        },
    }

    return service.create(datasource=payload, token=token)


def create_prediction(
    service: QandaPredictionService, token: str, query: str, user_id: str = None
) -> Prediction:
    payload = {"query": query, "save": True}

    return service.create(payload=payload, token=token, user_id=user_id)
