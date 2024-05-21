from typing import Tuple

from nesis.api.core.models.entities import UserRole, Role
from nesis.api.core.services import (
    UserService,
    UserSessionService,
    RoleService,
    UserRoleService,
    AppService,
)


def create_user_session(service: UserSessionService, email, password):
    admin_data = {
        "password": password,
        "email": email,
    }
    return service.create(session=admin_data)


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
    service.update(token=token, app_id=app_id, user={"roles": [role["id"]]})
