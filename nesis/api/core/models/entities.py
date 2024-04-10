import copy
import uuid
import enum
import datetime as dt
from typing import Optional
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


class Model(Base):
    __tablename__ = "model"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), nullable=False)
    module = Column(Enum(Module, name="model_module"), nullable=False)
    datasource = Column(Unicode(255), nullable=False)
    dataobject = Column(Unicode(255), nullable=False)
    target = Column(Unicode(255))
    enabled = Column(Boolean, default=True, nullable=False)
    attributes = Column(JSONB)

    __table_args__ = (
        Index("idx_model_name", "module", "name"),
        UniqueConstraint("module", "name", name="uq_model_module_name"),
    )

    def __init__(self, name, module, datasource, dataobject, target, attributes=None):
        self.name = name
        self.module = module
        self.datasource = datasource
        self.dataobject = dataobject
        self.target = target
        self.attributes = attributes

    def to_dict(self):
        dict_value = {
            "name": self.name,
            "module": self.module.name,
            "datasource": self.datasource,
            "dataobject": self.dataobject,
            "target": self.target,
            "enabled": self.enabled,
            "attributes": self.attributes,
        }
        return dict_value


class Rule(Base):
    __tablename__ = "model_rule"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), unique=True)
    model = Column(
        BigInteger,
        ForeignKey("model.id", ondelete="CASCADE", name="fk_model_rule_model"),
        nullable=False,
    )
    description = Column(Unicode(255))
    created_by = Column(Unicode(255))
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    value = Column(JSONB, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    rule_model = relationship("Model", foreign_keys=[model], lazy="subquery")

    def __init__(
        self, name, description, model, value, create_by=None, create_date=None
    ):
        self.name = name
        self.model = model
        self.description = description
        self.created_by = create_by
        self.value = value
        self.create_date = create_date or dt.datetime.utcnow()

    def to_dict(self):
        dict_value = {
            "id": self.id,
            "name": self.name,
            "model": {"id": self.model, "name": self.rule_model.name},
            "description": self.description,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
            "created_by": self.created_by,
            "value": self.value,
            "enabled": self.enabled,
        }
        return dict_value


class Prediction(Base):
    __tablename__ = "prediction"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    input = Column(JSONB)
    model = Column(
        BigInteger,
        ForeignKey("model.id", ondelete="CASCADE", name="fk_rule_model"),
        nullable=True,
    )
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)
    data = Column(JSONB, nullable=False)
    uid = Column(Unicode(4096), unique=True)
    module = Column(Unicode(4096))

    prediction_model = relationship("Model", foreign_keys=[model], lazy="subquery")

    def __init__(self, module, model, data, input, create_date=None, uid=None):
        self.module = module
        self.model = model
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


class DatasourceStatus(enum.Enum):
    ONLINE = enum.auto()
    OFFLINE = enum.auto()


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
        connection.pop("password", None)
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
        UniqueConstraint("uuid", "base_uri", name="uq_document_uuid_base_url"),
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
    create_date = Column(DateTime, default=dt.datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("name", name="uq_role_name"),)

    def __init__(self, name: str) -> None:
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.policy_items = []

    def to_dict(self, **kwargs) -> dict:
        dict_value = {
            "name": self.name,
            "id": self.uuid,
            "create_date": self.create_date.strftime(DEFAULT_DATETIME_FORMAT),
        }

        if (
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
