import copy
import uuid
import enum
import datetime as dt
from typing import Optional, Dict, Any
import nesis.api.core.models.objects as objects

from sqlalchemy.orm import relationship

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy import (
    Column,
    BigInteger,
    ForeignKey,
    Index,
    Boolean,
    UniqueConstraint,
    LargeBinary,
    DateTime,
    Unicode,
    Enum,
    ForeignKeyConstraint,
)

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

from . import Base


class Module(enum.Enum):
    anomaly = enum.auto()
    insights = enum.auto()
    data = enum.auto()
    qanda = enum.auto()


class Prediction(Base):
    __tablename__ = "prediction"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    input = Column(JSONB)
    model = Column(
        BigInteger,
        nullable=True,
    )
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    data = Column(JSONB, nullable=False)
    uid = Column(Unicode(4096), unique=True)
    module = Column(Unicode(4096))

    def __init__(self, module, data, input, create_date=None, uid=None):
        self.module = module
        self.input = input
        self.data = data
        self.uid = uid
        self.create_date = create_date or dt.datetime.utcnow()

    def to_dict(self, **kwargs):
        exclude = kwargs.get("exclude")
        exclude_fields = []
        if exclude:
            exclude_fields = exclude.split(",")
        dict_value = {
            "id": self.uid,
            "module": self.module,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
            "input": self.input if "input" not in exclude_fields else None,
            "data": self.data if "data" not in exclude_fields else None,
        }
        return dict_value


class Setting(Base):
    __tablename__ = "setting"
    id = Column(Unicode(255), primary_key=True, nullable=False)
    name = Column(Unicode(255), nullable=False, unique=True)
    module = Column(Unicode(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    attributes = Column(JSONB)

    def __init__(self, module: str, name: str, attributes: dict):
        self.id = str(uuid.uuid4())
        self.module = module
        self.name = name
        self.attributes = attributes

    def to_dict(self, **kwargs) -> dict:
        exclude = kwargs.get("exclude")
        exclude_fields = []
        if exclude:
            exclude_fields = exclude.split(",")
        dict_value = {
            "id": self.id,
            "name": self.name,
            "module": self.module,
            "enabled": self.enabled,
            "attributes": self.attributes,
        }

        return dict_value


class DatasourceType(enum.Enum):
    MINIO = enum.auto()
    POSTGRES = enum.auto()
    WINDOWS_SHARE = enum.auto()
    SQL_SERVER = enum.auto()
    GOOGLE_DRIVE = enum.auto()
    SHAREPOINT = enum.auto()
    MYSQL = enum.auto()
    DROPBOX = enum.auto()
    S3 = enum.auto()


class DatasourceStatus(enum.Enum):
    ONLINE = enum.auto()
    OFFLINE = enum.auto()
    INGESTING = enum.auto()


class Datasource(Base):
    __tablename__ = "datasource"
    id = Column(BigInteger, primary_key=True, nullable=False)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    type = Column(Enum(DatasourceType, name="datasource_type"), nullable=False)
    name = Column(Unicode(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(DatasourceStatus, name="datasource_status"), nullable=False)
    connection = Column(JSONB, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_datasource_name"),)

    def __init__(
        self,
        source_type: DatasourceType,
        name: str,
        status: DatasourceStatus = DatasourceStatus.ONLINE,
        connection: Optional[dict] = None,
    ):
        self.type = source_type
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.status = status
        self.connection = connection

    def to_dict(self, **kwargs) -> dict:
        connection = copy.deepcopy(self.connection or {})
        secret_keys = ["password", "certificate", "thumbprint"]
        for secret_key in secret_keys:
            connection.pop(secret_key, None)
        dict_value = {
            "id": self.uuid,
            "name": self.name,
            "type": self.type.name.lower(),
            "enabled": self.enabled,
            "connection": connection,
            "status": self.status.name.lower(),
        }

        return dict_value


class Document(Base):
    __tablename__ = "document"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(Unicode(255), nullable=False)
    # This is likely the endpoint e.g. hostname, URL, SambaShare e.t.c
    base_uri = Column(Unicode(255), nullable=False)
    filename = Column(Unicode(255), nullable=False)
    rag_metadata = Column(JSONB, nullable=False)
    store_metadata = Column(JSONB)

    __table_args__ = (
        UniqueConstraint(
            "uuid", "base_uri", "filename", name="uq_document_uuid_base_url_filename"
        ),
    )

    def __init__(
        self,
        document_id: str,
        filename: str,
        rag_metadata: dict,
        store_metadata: dict,
        base_uri: str,
    ) -> None:
        self.uuid = document_id
        self.base_uri = base_uri
        self.filename = filename
        self.rag_metadata = rag_metadata
        self.store_metadata = store_metadata

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            "id": self.uuid,
            "filename": self.filename,
            "rag_metadata": self.rag_metadata,
            "store_metadata": self.store_metadata,
        }

        return dict_value


# RBAC
class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    name = Column(Unicode(255), nullable=False)
    root = Column(Boolean, nullable=False, default=False)
    email = Column(Unicode(255), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    password = Column(LargeBinary, nullable=False)
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    attributes = Column(JSONB)

    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    def __init__(
        self,
        name: str,
        email: str,
        password: bytes,
        root=False,
        attributes: Optional[dict] = None,
        enabled: Boolean = True,
    ) -> None:
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.root = root
        self.enabled = enabled
        self.email = email
        self.password = password
        self.attributes = attributes
        self.roles = []

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            "id": self.uuid,
            "name": self.name,
            "email": self.email,
            "root": self.root,
            "enabled": self.enabled,
            "attributes": self.attributes,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
        }

        if hasattr(self, "roles") and self.roles:
            dict_value["roles"] = [role.to_dict() for role in self.roles or []]

        return dict_value


class Action(enum.Enum):
    READ = enum.auto()
    DELETE = enum.auto()
    CREATE = enum.auto()
    UPDATE = enum.auto()


class Role(Base):
    __tablename__ = "role"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    name = Column(Unicode(255), nullable=False)
    policy = Column(JSONB)
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_role_name"),)

    def __init__(self, name: str, policy: Dict[str, Any]) -> None:
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.policy = policy
        self.policy_items = []

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            "name": self.name,
            "id": self.uuid,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
        }

        if self.policy is not None:
            dict_value["policy"] = self.policy
        elif (
            hasattr(self, "policy_items")
            and self.policy_items
            and len(self.policy_items) > 0
        ):
            dict_value["policy"] = {
                "items": [action.to_dict() for action in self.policy_items]
            }

        return dict_value


class UserRole(Base):
    __tablename__ = "user_role"
    id = Column(BigInteger, primary_key=True, nullable=False)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    role = Column(BigInteger, nullable=False)
    user = Column(BigInteger, nullable=False)
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user", "role", name="uq_user_role_user_role"),
        ForeignKeyConstraint(
            ("role",), [Role.id], name="fk_user_role_role", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ("user",), [User.id], name="fk_user_role_user", ondelete="CASCADE"
        ),
    )

    def __init__(self, role: Role, user: User):
        self.uuid = str(uuid.uuid4())
        self.role = role.id
        self.user = user.id

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            "id": self.uuid,
            "role": self.role,
            "user": self.user,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
        }

        return dict_value


class RoleAction(Base):
    __tablename__ = "role_action"
    id = Column(BigInteger, primary_key=True, nullable=False)
    role = Column(BigInteger, nullable=False)
    action = Column(Enum(Action, name="role_action_action"), nullable=False)
    resource_type = Column(
        Enum(objects.ResourceType, name="role_action_resource_type"), nullable=False
    )
    resource = Column(Unicode(1024))

    __table_args__ = (
        UniqueConstraint(
            "role",
            "action",
            "resource_type",
            "resource",
            name="uq_role_action_resource_type_resource",
        ),
        ForeignKeyConstraint(
            ("role",), [Role.id], name="fk_role_action_role", ondelete="CASCADE"
        ),
    )

    def __init__(
        self,
        role: Role | None,
        action: Action,
        resource_type: objects.ResourceType,
        resource: str,
    ):
        self.action = action.name
        if role:
            self.role = role.id
        self.resource = resource
        self.action = action
        self.resource_type = resource_type

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            # "id": self.id,
            "action": self.action.name.lower(),
            "resource": f"{self.resource_type.name.lower()}/{self.resource or '*'}",
        }

        return dict_value


class Task(Base):
    """
    This entity represents a background task to be run on schedule
    """

    __tablename__ = "task"
    id = Column(BigInteger, primary_key=True, nullable=False)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    type = Column(Enum(objects.TaskType, name="task_type"), nullable=False)
    schedule = Column(Unicode(255), nullable=False)
    """
    This basically the entity that this task operates on if any. For example a datasource.
    We cannot put a foreign on this field since the parent could be of different entity/object types.
    Having a parent id here helps us find all the tasks related to a parent. For example if a parent is deleted,
    all related tasks should be deleted.
    """
    parent_id = Column(Unicode(255))
    definition = Column(JSONB, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(Enum(objects.TaskStatus, name="task_status"), nullable=False)
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    update_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "parent_id", "type", "schedule", name="uq_task_parent_id_type_schedule"
        ),
        Index("idx_task_type", "type"),
        Index("idx_task_parent", "parent_id"),
    )

    def __init__(
        self,
        task_type: objects.TaskType,
        schedule: str,
        definition: Dict[str, Any],
        status: objects.TaskStatus = objects.TaskStatus.CREATED,
        create_date: dt.datetime = dt.datetime.utcnow(),
        parent_id: Optional[str] = None,
    ):
        self.uuid = str(uuid.uuid4())
        self.type = task_type
        self.status = status
        self.schedule = schedule
        self.definition = definition
        self.create_date = create_date
        self.parent_id = parent_id

    def to_dict(self, **kwargs):
        return {
            "id": self.uuid,
            "type": self.type.name,
            "schedule": self.schedule,
            "enabled": self.enabled,
            "status": self.status.name,
            "parent_id": self.parent_id,
            "definition": self.definition,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
            "update_date": self.update_date.strftime(DEFAULT_DATETIME_FORMAT),
        }


class App(Base):
    """
    An app integration
    """

    __tablename__ = "app"
    id = Column(BigInteger, primary_key=True, nullable=False)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    name = Column(Unicode(255))
    description = Column(Unicode(255))
    secret = Column(LargeBinary, nullable=False)
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    attributes = Column(JSONB)
    enabled = Column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_app_name"),)

    def __init__(
        self,
        name: str,
        secret: bytes,
        description: str,
        create_date: dt.datetime = dt.datetime.utcnow(),
    ):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.secret = secret
        self.description = description
        self.create_date = create_date
        self.roles = []

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        result = {
            "id": self.uuid,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
        }
        if isinstance(self.secret, str) and "secret" in (kwargs.get("include") or []):
            result["secret"] = self.secret
        if hasattr(self, "roles") and self.roles:
            result["roles"] = [role.to_dict() for role in self.roles or []]

        return result


class AppRole(Base):
    __tablename__ = "app_role"
    id = Column(BigInteger, primary_key=True, nullable=False)
    uuid = Column(Unicode(255), unique=True, nullable=False)
    role = Column(BigInteger, nullable=False)
    app = Column(BigInteger, nullable=False)
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("app", "role", name="uq_app_role_app_role"),
        ForeignKeyConstraint(
            ("role",), [Role.id], name="fk_app_role_role", ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ("app",), [App.id], name="fk_app_role_app", ondelete="CASCADE"
        ),
    )

    def __init__(self, role: Role, app: App):
        self.uuid = str(uuid.uuid4())
        self.role = role.id
        self.app = app.id

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            "id": self.uuid,
            "role": self.role,
            "app": self.app,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
        }

        return dict_value
