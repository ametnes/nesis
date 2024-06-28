import os
from nesis.api.core.models.entities import (
    Action,
    UserRole,
    RoleAction,
    User,
    Datasource,
    Task,
    AppRole,
    App,
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
from nesis.api.core.services.util import PermissionException, UnauthorizedAccess
from nesis.api.core.services.app_service import AppService


qanda_prediction_service: QandaPredictionService
datasource_service: DatasourceService
settings_service: SettingsService
user_service: UserService
user_session_service: UserSessionService
role_service: RoleService
task_service: TaskService
app_service: AppService


def init_services(config, http_client=None):
    global datasource_service, qanda_prediction_service, settings_service, user_service, user_session_service, role_service, task_service, app_service

    user_session_service = UserSessionService(config=config)

    qanda_prediction_service = QandaPredictionService(
        config=config, client=http_client, session_service=user_session_service
    )
    settings_service = SettingsService(
        config=config, session_service=user_session_service
    )

    user_service = UserService(
        config=config,
        session_service=user_session_service,
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

    app_service = AppService(config=config, session_service=user_session_service)

    # Initialize system
    init_system(config=config)


def authorized(
    session_service,
    session: Session,
    token: str,
    action: Action,
    resource_type: ResourceType,
    resource: str = None,
    **kwargs,
) -> dict:
    """
    This function checks if a given session token (app or user) is allowed to perform a given action on the resource (if supplied).
    If no resource is supplied, then the check is performed on all resources
    :param session_service: The session service
    :param session: The DBSession
    :param token: The token
    :param action: The action attempted
    :param resource_type: The resource type
    :param resource: The resource
    :param kwargs: Any extra args such
    :return: The session object
    """
    user_session = session_service.get(token=token)
    session_user = user_session.get("user")
    session_app = user_session.get("app")
    user_id = kwargs.get("user_id")

    if not any([session_app, session_user]):
        raise UnauthorizedAccess()

    # if this a root user, permit all actions
    if session_user is not None and session_user.get("root", False):
        return session_user

    query = _get_action_query(
        action, resource, resource_type, session, session_app, session_user, user_id
    )

    if query is None:
        raise UnauthorizedAccess()

    role_actions = query.all()
    if len(role_actions) == 0:
        message = (
            f"Not authorized to perform {action.name} on {resource}"
            if resource
            else f"Not authorized to perform {action.name} on {resource_type.name}"
        )
        raise PermissionException(message)

    return session_user or session_app


def _get_action_query(
    action, resource, resource_type, session, session_app, session_user, user_id
):
    # noinspection PyTypeChecker
    query = (
        session.query(RoleAction)
        .filter(RoleAction.action == action)
        .filter(RoleAction.resource_type == resource_type)
    )

    # if a user_id is supplied as well the session_app, then we use the user's permission (aka. AssumeUser)
    if all([user_id, session_app]) or session_user is not None:
        _user_id = user_id
        if session_user is not None:
            _user_id = session_user["id"]

        query = (
            query.filter(RoleAction.role == UserRole.role)
            .filter(UserRole.user == User.id)
            .filter(User.uuid == _user_id)
        )
    elif session_app is not None:
        query = (
            query.filter(RoleAction.role == AppRole.role)
            .filter(AppRole.app == App.id)
            .filter(App.uuid == session_app["id"])
        )
    else:
        query = None
    if resource:
        query = query.filter(RoleAction.resource.in_([resource, "*"]))
    return query


def authorized_resources(
    session_service,
    session: Session,
    token: str,
    action: Action,
    resource_type: ResourceType,
    **kwargs,
) -> list[RoleAction]:
    user_session = session_service.get(token=token)
    session_user = user_session.get("user")
    session_app = user_session.get("app")
    user_id = kwargs.get("user_id")

    if not any([session_app, session_user]):
        raise UnauthorizedAccess()
    query = _get_action_query(
        action=action,
        resource=None,
        resource_type=resource_type,
        session=session,
        session_app=session_app,
        session_user=session_user,
        user_id=user_id,
    )

    def get_enabled_datasources():
        return session.query(Datasource).filter(Datasource.enabled.is_(True)).all()

    def get_enabled_tasks():
        return session.query(Task).filter(Task.enabled.is_(True)).all()

    def get_enabled_apps():
        return session.query(App).filter(App.enabled.is_(True)).all()

    # If root, return all actions
    if session_user is not None and session_user.get("root") or False:
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
            case ResourceType.APPS:
                apps = get_enabled_apps()
                return [
                    RoleAction(
                        action=action,
                        resource_type=resource_type,
                        resource=app.uuid,
                        role=None,
                    )
                    for app in apps
                ]
            case _:
                raise util.PermissionException("Unauthorized resource type")

    action_list = []
    dss = None
    tasks = None
    apps = None
    # If not root, return only actions permitted
    for role_action in query.all():
        # If wildcard, then we return all resources
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
                case ResourceType.APPS:
                    if apps is None:
                        apps = get_enabled_apps()
                    action_list += [
                        RoleAction(
                            action=Action[role_action.action.name],
                            resource_type=resource_type,
                            resource=app.uuid,
                            role=None,
                        )
                        for app in apps
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
