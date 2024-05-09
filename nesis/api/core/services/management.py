import json
import os
from typing import Optional, List

import bcrypt
import memcache
from sqlalchemy.orm import Session
from strgen import StringGenerator as SG

import logging
import nesis.api.core.services as services
from nesis.api.core.models import DBSession
from nesis.api.core.models.objects import ResourceType, UserSession
from nesis.api.core.models.entities import User, Role, RoleAction, UserRole, Action
from nesis.api.core.services.util import (
    ServiceOperation,
    ServiceException,
    ConflictException,
    UnauthorizedAccess,
)

_LOG = logging.getLogger(__name__)


class UserSessionService(ServiceOperation):
    """
    Manage user sessions
    """

    def __init__(self, config):
        self.__config = config
        self.__enable_user_verification = config.get("verify_users", False)
        self.__verify_users_override = config.get("verify_users_override", False)
        self.__cache = memcache.Client(config["memcache"]["hosts"], debug=1)
        self.__LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def get(self, **kwargs):
        token = kwargs.get("token")
        if token is None:
            raise UnauthorizedAccess("Token not supplied")

        key = self.__cache_key(token)
        value = self.__cache.get(key)

        if value is None:
            raise UnauthorizedAccess("Invalid token")

        return {"token": token, "user": value}

    def delete(self, **kwargs):
        token = kwargs["token"]
        session = self.get(**kwargs)
        if session["token"] != token:
            raise UnauthorizedAccess("Invalid session token")
        self.__cache.delete(self.__cache_key(token))

    @staticmethod
    def __cache_key(key):
        return f"sessions/{key}"

    def create(self, **kwargs) -> UserSession:
        user_session = kwargs["session"]
        session = DBSession()
        session.expire_on_commit = False

        self.__LOG.debug(f"Received session object {kwargs}")
        email = user_session.get("email")
        password = user_session.get("password")
        session_oauth_token_value = user_session.get(
            os.environ.get("NESIS_OAUTH_TOKEN_KEY")
        )
        oauth_token_value = os.environ.get("NESIS_OAUTH_TOKEN_VALUE")

        try:

            if all([email, password]):
                users = session.query(User).filter_by(email=email).all()
                if len(users) != 1:
                    raise UnauthorizedAccess("User not found")
                user_dict = users[0].to_dict()
                attributes = user_dict["attributes"]

                # password based auth
                db_pass = users[0].password
                user_password = password.encode("utf-8")
                if not bcrypt.checkpw(user_password, db_pass):
                    raise UnauthorizedAccess("Invalid email/password")
                # update last login details.
                db_user = users[0]

                return self.__create_user_session(db_user)
            elif all([email, session_oauth_token_value, oauth_token_value]):
                if session_oauth_token_value != oauth_token_value:
                    raise UnauthorizedAccess("Invalid oauth token value")
                secrets = SG(r"[\l\d]{30}").render_list(1, unique=True)

                try:
                    entity = _create_user(
                        root=False,
                        session=session,
                        user={**user_session, "password": secrets[0]},
                    )
                    # update last login details.
                    db_user = entity
                except ConflictException:
                    db_user = session.query(User).filter_by(email=email).first()
                return self.__create_user_session(db_user)
            else:
                raise UnauthorizedAccess("Missing email and password")

        finally:
            if session:
                session.close()

    def __create_user_session(self, db_user: User):
        user_dict = db_user.to_dict()
        token = SG("[\l\d]{128}").render()
        session_token = self.__cache_key(token)
        expiry = (
            self.__config["memcache"].get("session", {"expiry": 0}).get("expiry", 0)
        )
        if self.__cache.get(session_token) is None:
            self.__cache.set(session_token, user_dict, time=expiry)
        while self.__cache.get(session_token)["id"] != user_dict["id"]:
            token = SG("[\l\d]{128}").render()
            session_token = self.__cache_key(token)
            self.__cache.set(session_token, user_dict, time=expiry)
        return UserSession(token=token, expiry=expiry, user=db_user)

    def update(self, **kwargs):
        raise NotImplementedError("Invalid operation on datasource")


def _create_user(session: Session, user: dict, root: bool):
    name = user.get("name")
    email = user.get("email")
    password = user.get("password")
    if not all([email, password, name]):
        raise ServiceException("name, email and password must be supplied")
    password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    entity = User(name=name, email=email, password=password, root=root)
    session.add(entity)

    try:
        session.commit()
        session.refresh(entity)
    except Exception as exc:
        session.rollback()
        error_str = str(exc).lower()

        if ("unique constraint" in error_str) and ("uq_user_email" in error_str):
            # valid failure
            raise ConflictException("User already exists")
        else:
            raise
    return entity


class UserService(ServiceOperation):
    """
    Manage system users
    """

    def __init__(self, config: dict, session_service: UserSessionService) -> None:
        self._config = config
        self._resource_type = ResourceType.USERS
        self._session_service = session_service
        self._user_role_service = UserRoleService(
            config, session_service=session_service
        )

        self._LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._LOG.info("Initializing service...")

    def create(self, **kwargs):
        user: dict = kwargs["user"]
        root = kwargs.get("root", False)

        session = DBSession()
        try:
            session.expire_on_commit = False

            users = session.query(User).all()
            # First user will be the root user
            if len(users) == 0:
                root = True
            else:
                if root:
                    self._LOG.info(
                        f"System already initialized, skipping admin user creation"
                    )
                    return
                services.authorized(
                    session_service=self._session_service,
                    session=session,
                    token=kwargs.get("token"),
                    action=Action.CREATE,
                    resource_type=self._resource_type,
                )

            entity = _create_user(root=root, session=session, user=user)

            if not root:
                for user_role in user.get("roles") or []:
                    self._user_role_service.create(
                        **kwargs, user_id=entity.uuid, role={"id": user_role}
                    )

            return entity
        finally:
            if session:
                session.close()

    def get(self, **kwargs):
        user_id = kwargs.get("user_id")

        session = DBSession()

        services.authorized(
            session_service=self._session_service,
            session=session,
            token=kwargs.get("token"),
            action=Action.READ,
            resource_type=self._resource_type,
        )

        try:
            session.expire_on_commit = False
            query = session.query(User)
            if user_id:
                query = query.filter(User.uuid == user_id)

            results = query.all()

            if user_id:
                roles = (
                    session.query(UserRole)
                    .filter(UserRole.user == User.id)
                    .filter(User.uuid == user_id)
                    .all()
                )
                if len(roles) > 0 and len(results) > 0:
                    results[0].roles = roles

            return results
        except:
            self._LOG.exception("Error when fetching users")
            raise
        finally:
            if session:
                session.close()

    @staticmethod
    def get_user(session, **kwargs) -> User:
        email = kwargs.get("email")
        if email:
            return session.query(User).filter(User.email == email).first()
        user_id = kwargs.get("user_id")
        if user_id:
            return session.query(User).filter(User.uuid == user_id).first()

    def delete(self, **kwargs):
        uuid = kwargs["user_id"]
        session = DBSession()

        services.authorized(
            session_service=self._session_service,
            session=session,
            token=kwargs.get("token"),
            action=Action.READ,
            resource_type=self._resource_type,
        )

        try:
            session.expire_on_commit = False
            user: User = session.query(User).filter(User.uuid == uuid).first()
            if user and user.root:
                raise ServiceException("Cannot delete Administrator")
            session.delete(user)
            session.commit()
        except Exception as e:
            self._LOG.exception("Error when fetching users")
            raise
        finally:
            if session:
                session.close()

    def __get_rbac_resource(self, user_id):
        return f"{self._resource_type}/{user_id}"

    def update(self, **kwargs):
        uuid = kwargs["user_id"]
        user: dict = kwargs["user"]

        session = DBSession()

        services.authorized(
            session_service=self._session_service,
            session=session,
            token=kwargs.get("token"),
            action=Action.UPDATE,
            resource_type=self._resource_type,
            resource=self.__get_rbac_resource(user_id=uuid),
        )

        try:
            session.expire_on_commit = False

            name = user.get("name")
            email = user.get("email")
            enabled = user.get("enabled")
            password: str = user.get("password")

            user_record: User = session.query(User).filter(User.uuid == uuid).first()

            user_record.name = name or user_record.name

            if enabled is not None:
                if user and user_record.root and not enabled:
                    raise ServiceException("Cannot disable Administrator")
                user_record.enabled = enabled
            user_record.email = email or user_record.email
            if password and password.strip() != "":
                user_record.password = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                )

            session.merge(user_record)
            session.commit()

            self._user_role_service.delete(**{**kwargs, "user_id": uuid})

            for user_role in user.get("roles") or []:
                try:
                    self._user_role_service.create(**kwargs, role={"id": user_role})
                except ConflictException as ex:
                    self._LOG.info(ex)

            return user_record
        except Exception as e:
            session.rollback()
            self._LOG.exception(f"Error when updating user")
            raise
        finally:
            if session:
                session.close()

    def get_roles(self, **kwargs):
        uuid = kwargs["user_id"]

        session = DBSession()

        services.authorized(
            session_service=self._session_service,
            session=session,
            token=kwargs.get("token"),
            action=Action.READ,
            resource_type=self._resource_type,
            resource=self.__get_rbac_resource(user_id=uuid),
        )

        return self._user_role_service.get(**kwargs)

    def delete_role(self, **kwargs):
        uuid = kwargs["user_id"]

        session = DBSession()

        services.authorized(
            session_service=self._session_service,
            session=session,
            token=kwargs.get("token"),
            action=Action.READ,
            resource_type=self._resource_type,
            resource=self.__get_rbac_resource(user_id=uuid),
        )

        return self._user_role_service.delete(**kwargs)


class RoleService(ServiceOperation):
    """
    Manage system roles
    """

    def __init__(self, config: dict, session_service: UserSessionService):
        self.__resource_type = ResourceType.ROLES
        self.__config = config
        self.__session_service = session_service
        self.__LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self.__LOG.info("Initializing service...")

    def create(self, **kwargs) -> Role:
        role: dict = kwargs["role"]

        session = DBSession()
        try:
            session.expire_on_commit = False

            services.authorized(
                session_service=self.__session_service,
                session=session,
                token=kwargs.get("token"),
                action=Action.CREATE,
                resource_type=self.__resource_type,
            )

            name = role.get("name")
            role_policy = role.get("policy")

            if not all([name, role_policy]):
                raise ServiceException("name and policy must be supplied")

            if isinstance(role_policy, str):
                try:
                    role_policy = json.loads(role_policy)
                except ValueError:
                    raise ServiceException("Invalid role policy")

            if not isinstance(role_policy, dict):
                raise ServiceException("Invalid policy document")

            role_action_list = []

            try:
                role_actions = role_policy.get("items")
                if role_actions is None:
                    raise ValueError
            except ValueError:
                raise ServiceException("Invalid role policy")

            for action in role_actions:
                action_resource: Optional[str] = action.get("resource")
                action_resources: Optional[List[str]] = action.get("resources") or []
                if action_resource:
                    action_resources.append(action_resource)
                action_action: Optional[str] = action.get("action")

                if action_action is None or len(action_resources) == 0:
                    raise ServiceException("resource or resources must be supplied")

                for action_resource in action_resources:
                    action_resource_parts = action_resource.split("/")
                    resource_type = action_resource_parts[0]
                    resource_item = None
                    if len(action_resource_parts) > 1:
                        resource_item = action_resource_parts[1]
                    role_action = RoleAction(
                        action=Action[action_action.upper()],
                        role=None,
                        resource=resource_item,
                        resource_type=ResourceType[resource_type.upper()],
                    )
                    role_action_list.append(role_action)

            if len(role_action_list) == 0:
                raise ServiceException("Invalid role. Policy not supplied")

            role_record: Role = Role(name=name)
            session.add(role_record)
            session.commit()
            session.refresh(role_record)

            for role_action in role_action_list:
                role_action.role = role_record.id
                session.add(role_action)
            session.commit()

            role_record.policy = role_action_list

            return role_record
        except Exception as exc:
            session.rollback()
            error_str = str(exc).lower()

            if ("unique constraint" in error_str) and ("uq_role_name" in error_str):
                # valid failure
                raise ConflictException("Role name already exists")
            else:
                raise
        finally:
            if session:
                session.close()

    def get(self, **kwargs) -> list[Role]:
        uuid = kwargs.get("id")
        session = DBSession()
        try:
            session.expire_on_commit = False

            services.authorized(
                session_service=self.__session_service,
                session=session,
                token=kwargs.get("token"),
                action=Action.READ,
                resource_type=self.__resource_type,
            )

            query = session.query(Role, RoleAction).filter(Role.id == RoleAction.role)
            if uuid:
                query = query.filter(Role.uuid == uuid)

            result = {}
            for role, role_action in query.all():
                role_id = role.id
                try:
                    result_role: Role = result[role_id]
                except KeyError:
                    result_role = role
                    result[role_id] = role

                if not hasattr(result_role, "policy_items"):
                    result_role.policy_items = []

                result_role.policy_items.append(role_action)

            return list(result.values())
        except:
            self.__LOG.exception("Error when fetching users")
            raise
        finally:
            if session:
                session.close()

    def delete(self, **kwargs):
        uuid = kwargs["id"]
        session = DBSession()
        try:
            session.expire_on_commit = False

            services.authorized(
                session_service=self.__session_service,
                session=session,
                token=kwargs.get("token"),
                action=Action.DELETE,
                resource_type=self.__resource_type,
            )

            query = session.query(Role).filter(Role.uuid == uuid)
            query.delete()
            session.commit()
        except Exception as e:
            self.__LOG.exception("Error when fetching users")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs) -> Role:
        role_uuid = kwargs["id"]
        role: dict = kwargs["role"]

        session = DBSession()
        try:
            session.expire_on_commit = False

            services.authorized(
                session_service=self.__session_service,
                session=session,
                token=kwargs.get("token"),
                action=Action.UPDATE,
                resource_type=self.__resource_type,
            )

            role_record = session.query(Role).filter(Role.uuid == role_uuid).first()
            if role_record is None:
                raise ServiceException(f"Invalid role is {role_uuid}")

            if role.get("policy") and isinstance(role.get("policy"), str):
                try:
                    role_actions: Optional[dict] = json.loads(
                        role.get("policy") or "{}"
                    )
                except ValueError:
                    role_actions: Optional[dict] = role.get("policy")
            else:
                role_actions: Optional[dict] = {}

            if not isinstance(role_actions, dict):
                raise ServiceException("Invalid policy document")

            role_action_items = []
            for action in role_actions.get("items") or []:
                action_resource: Optional[str] = action.get("resource")
                action_action: Optional[str] = action.get("action")
                action_actions: Optional[set[str]] = action.get("actions") or set()
                action_resources: Optional[set[str]] = action.get("resources") or set()

                if not any([action_resource, action_resources]):
                    raise ServiceException("resource or resources must be supplied")

                if action_resource:
                    action_resources.add(action_resource)

                if action_action:
                    action_actions.add(action_action)

                for action_resource in action_resources:
                    action_resource_parts = action_resource.split("/")
                    action_resource_type = ResourceType[
                        action_resource_parts[0].upper()
                    ]
                    for action_actions_action in action_actions:
                        role_action = RoleAction(
                            action=Action[action_actions_action.upper()],
                            role=role_record,
                            resource=action_resource_parts[1],
                            resource_type=action_resource_type,
                        )
                        role_action_items.append(role_action)

            # First delete all role actions for this role
            session.query(RoleAction).filter(RoleAction.role == Role.id).filter(
                Role.uuid == role_uuid
            ).delete()
            session.commit()

            # Add new role actions
            for role_action in role_action_items:
                session.add(role_action)
            session.commit()

            return role_record

        except Exception as exc:
            session.rollback()
            error_str = str(exc).lower()

            if ("unique constraint" in error_str) and ("uq_role_name" in error_str):
                # valid failure
                raise ConflictException("Role name already exists")
            else:
                raise
        finally:
            if session:
                session.close()


class UserRoleService(ServiceOperation):
    """
    Manage user roles. This is a function of the user service. Permissions are part of the user function.
    Whatever a user is permitted to do on a user, they are permitted to do on the user role.
    For this reason, we don't check/test permissions in the user role service as it is called only in the user service.
    """

    def __init__(self, config: dict, session_service: UserSessionService):
        self.__resource_type = ResourceType.USERS
        self.__config = config
        self.__session_service = session_service
        self.__LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self.__LOG.info("Initializing service...")

    def create(self, **kwargs) -> UserRole:
        user_id: str = kwargs["user_id"]
        user_role: dict = kwargs["role"]

        session = DBSession()
        try:
            session.expire_on_commit = False

            role: Role = (
                session.query(Role).filter(Role.uuid == user_role["id"]).first()
            )
            user: User = session.query(User).filter(User.uuid == user_id).first()

            if not all([role, user]):
                raise ServiceException("Invalid role or user")

            user_role: UserRole = UserRole(user=user, role=role)

            session.add(user_role)
            session.commit()
            session.refresh(user_role)

            return user_role
        except Exception as e:
            session.rollback()
            self.__LOG.exception(f"Error when creating role")

            error_str = str(e)

            if ("unique constraint" in error_str) and (
                "uq_user_role_user_role" in error_str
            ):
                # valid failure
                raise ConflictException("Role already attached to user")
            else:
                raise
        finally:
            if session:
                session.close()

    def get(self, **kwargs) -> list[UserRole]:
        user_id = kwargs.get("user_id")
        session = DBSession()
        try:
            session.expire_on_commit = False

            return (
                session.query(Role)
                .filter(Role.id == UserRole.role)
                .filter(UserRole.user == User.id)
                .filter(User.uuid == user_id)
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
        user_id = kwargs["user_id"]
        session = DBSession()
        try:
            session.expire_on_commit = False

            if uuid is None:
                query = (
                    session.query(UserRole)
                    .filter(UserRole.role == Role.id)
                    .filter(UserRole.user == User.id)
                    .filter(User.uuid == user_id)
                )
            else:
                query = (
                    session.query(UserRole)
                    .filter(UserRole.role == Role.id)
                    .filter(UserRole.user == User.id)
                    .filter(Role.uuid == uuid)
                    .filter(User.uuid == user_id)
                )
            query.delete()
            session.commit()
        except Exception as e:
            self.__LOG.exception("Error when fetching users")
            raise
        finally:
            if session:
                session.close()

    def update(self, **kwargs) -> UserRole:
        role_uuid = kwargs["id"]
        role: dict = kwargs["role"]

        session = DBSession()
        try:
            session.expire_on_commit = False

            role_record = session.query(Role).filter(Role.uuid == role_uuid)
            session.query(UserRole).filter(Role.uuid == role_uuid).filter(
                UserRole.role == Role.id
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
