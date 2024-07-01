import ast
import enum
from enum import Enum


class Datasource:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.dataobjects = kwargs.get("dataobjects")
        self.engine = kwargs.get("engine")
        self.status = kwargs.get("status")
        self.connection = None
        connection = kwargs.get("connection")
        if connection:
            self.connection = ast.literal_eval(connection)

    def to_dict(self, **kwargs):
        _dict = {
            "name": self.name,
            "dataobjects": self.dataobjects,
            "engine": self.engine,
            "status": self.status,
        }

        if self.connection:
            _dict["connection"] = {
                key: value
                for key, value in self.connection.items()
                if key not in ["password"]
            }

        return _dict


class DataObject:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name")
        self.fields = kwargs.get("fields")

    def to_dict(self, **kwargs):
        _dict = {
            "name": self.name,
            "fields": self.fields,
        }

        return _dict


class ResourceType(Enum):
    MODULES = enum.auto()
    USERS = enum.auto()
    DATASOURCES = enum.auto()
    ROLES = enum.auto()
    PREDICTIONS = enum.auto()
    SETTINGS = enum.auto()
    TASKS = enum.auto()
    APPS = enum.auto()


class UserSession:
    def __init__(self, token, user, expiry: str):
        self.token = token
        self.expiry = expiry
        self.user = user

    def to_dict(self, **kwargs):
        return {"token": self.token, "expiry": self.expiry, "user": self.user.to_dict()}


class TaskType(Enum):
    INGEST_DATASOURCE = enum.auto()


class TaskStatus(enum.Enum):
    RUNNING = enum.auto()
    PAUSED = enum.auto()
    COMPLETED = enum.auto()
    ERROR = enum.auto()
    CREATED = enum.auto()


class DatasourceStatus(enum.Enum):
    ONLINE = enum.auto()
    OFFLINE = enum.auto()
    INGESTING = enum.auto()


class DocumentStatus(enum.Enum):
    SUCCESS = enum.auto()
    PROCESSING = enum.auto()
    ERROR = enum.auto()


class Module(enum.Enum):
    anomaly = enum.auto()
    insights = enum.auto()
    data = enum.auto()
    qanda = enum.auto()


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
