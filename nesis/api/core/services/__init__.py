import os
from nesis.api.core.models.entities import (
    Action,
    UserRole,
    RoleAction,
    User,
    Datasource,
    Task,
)
from nesis.api.core.models.objects import ResourceType
from sqlalchemy.orm import Session
from nesis.api.core.services.settings import SettingsService
from nesis.api.core.services.datasources import DatasourceService
from nesis.api.core.services.predictions import (
    QandaPredictionService,
)
from nesis.api.core.services.management import (
    UserService,
    UserSessionService,
    RoleService,
    UserRoleService,
)
from nesis.api.core.services.task_service import TaskService
from nesis.api.core.services.util import PermissionException


qanda_prediction_service: QandaPredictionService
datasource_service: DatasourceService
settings_service: SettingsService
user_service: UserService
user_session_service: UserSessionService
role_service: RoleService
user_role_service: UserRoleService
task_service: TaskService


def init_services(config, http_client=None):
    global datasource_service, qanda_prediction_service, settings_service, user_service, user_session_service, role_service, user_role_service, task_service

    user_session_service = UserSessionService(config=config)

    qanda_prediction_service = QandaPredictionService(
        config=config, client=http_client, session_service=user_session_service
    )
    settings_service = SettingsService(
        config=config, session_service=user_session_service
    )

    user_role_service = UserRoleService(config, session_service=user_session_service)
    user_service = UserService(
        config=config,
        session_service=user_session_service,
        user_role_service=user_role_service,
    )
    role_service = RoleService(config=config, session_service=user_session_service)
    datasource_service = DatasourceService(
        config=config, session_service=user_session_service
    )

    task_service = TaskService(
        config=config,
        session_service=user_session_service,
        datasource_service=datasource_service,
        http_client=http_client,
    )

    datasource_service.task_service = task_service

    # Initialize system
    init_system(config=config)


def authorized(
    session_service,
    session: Session,
    token: str,
    action: Action,
    resource_type: ResourceType,
    resource: str = None,
) -> dict:
    user_session = session_service.get(token=token)
    session_user = user_session["user"]

    if session_user.get("root") or False:
        return session_user

    # noinspection PyTypeChecker
    query = (
        session.query(RoleAction)
        .filter(RoleAction.role == UserRole.role)
        .filter(RoleAction.action == action)
        .filter(RoleAction.resource_type == resource_type)
        .filter(UserRole.user == User.id)
        .filter(User.uuid == session_user["id"])
    )

    if resource:
        query = query.filter(RoleAction.resource == resource)

    user_role_actions = query.all()
    if len(user_role_actions) == 0:
        raise PermissionException(f"Not authorized to perform this action")

    return session_user


def authorized_resources(
    session_service,
    session: Session,
    token: str,
    action: Action,
    resource_type: ResourceType,
) -> list[RoleAction]:
    user_session = session_service.get(token=token)
    session_user = user_session["user"]

    # noinspection PyTypeChecker
    query = (
        session.query(RoleAction)
        .filter(RoleAction.role == UserRole.role)
        .filter(RoleAction.action == action)
        .filter(RoleAction.resource_type == resource_type)
        .filter(UserRole.user == User.id)
    )

    # If root, return all actions
    def get_enabled_datasources():
        return session.query(Datasource).filter(Datasource.enabled.is_(True)).all()

    def get_enabled_tasks():
        return session.query(Task).filter(Task.enabled.is_(True)).all()

    if session_user.get("root") or False:
        match resource_type:
            case ResourceType.DATASOURCES:
                dss = get_enabled_datasources()
                return [
                    RoleAction(
                        action=action,
                        resource_type=resource_type,
                        resource=ds.name,
                        role=None,
                    )
                    for ds in dss
                ]
            case ResourceType.TASKS:
                tasks = get_enabled_tasks()
                return [
                    RoleAction(
                        action=action,
                        resource_type=resource_type,
                        resource=ds.uuid,
                        role=None,
                    )
                    for ds in tasks
                ]
            case _:
                raise util.PermissionException("Unauthorized resource type")

    action_list = []
    dss = None
    tasks = None
    for role_action in query.filter(User.uuid == session_user["id"]).all():
        if role_action.resource and role_action.resource.strip() == "*":
            match resource_type:
                case ResourceType.DATASOURCES:
                    if dss is None:
                        dss = get_enabled_datasources()
                    action_list += [
                        RoleAction(
                            action=Action[role_action.action.name],
                            resource_type=resource_type,
                            resource=ds.name,
                            role=None,
                        )
                        for ds in dss
                    ]
                case ResourceType.TASKS:
                    if tasks is None:
                        tasks = get_enabled_tasks()
                    action_list += [
                        RoleAction(
                            action=Action[role_action.action.name],
                            resource_type=resource_type,
                            resource=ds.uuid,
                            role=None,
                        )
                        for ds in tasks
                    ]
                case _:
                    raise util.PermissionException("Unauthorized resource type")
        else:
            action_list.append(role_action)
    return action_list


def init_system(config: dict):
    # Create root user, if not exists
    user = {
        "name": "System Administrator",
        "email": os.environ.get("NESIS_ADMIN_EMAIL"),
        "password": os.environ.get("NESIS_ADMIN_PASSWORD"),
    }
    user_service.create(user=user, root=True)
