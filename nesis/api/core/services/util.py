import re
import abc
from typing import List, Union, Optional

from nesis.api.core.models import DBSession
from nesis.api.core.models.entities import Document
from nesis.api.core.util import isblank
from nesis.api.core.util.http import HttpClient

from apscheduler.triggers.cron import CronTrigger, BaseTrigger
from apscheduler.triggers.date import DateTrigger

import nesis.api.core.util.dateutil as du


class ServiceOperation(abc.ABC):
    @abc.abstractmethod
    def get(self, **kwargs):
        pass

    @abc.abstractmethod
    def create(self, **kwargs):
        pass

    @abc.abstractmethod
    def update(self, **kwargs):
        pass

    @abc.abstractmethod
    def delete(self, **kwargs):
        pass


class ServiceException(Exception):
    pass


class UnauthorizedAccess(Exception):
    pass


class PermissionException(Exception):
    pass


class ValidationException(Exception):
    pass


class ConflictException(Exception):
    pass


class InvalidMethodException(ServiceException):
    pass


class ConfigurationException(ServiceException):
    pass


class ObjectNotFound(ServiceException):
    pass


def save_document(**kwargs) -> Document:
    document = kwargs.get("document")
    if document is None:
        document = Document(
            document_id=kwargs["document_id"],
            filename=kwargs["filename"],
            rag_metadata=kwargs["rag_metadata"],
            store_metadata=kwargs["store_metadata"],
            base_uri=kwargs["base_uri"],
            last_modified=kwargs["last_modified"],
        )

    session = kwargs.get("session")
    if session is None:
        session = DBSession()
    try:
        session.expire_on_commit = False
        session.add(document)
        session.commit()
        session.refresh(document)
        return document
    except:
        session.rollback()
        raise
    finally:
        if session:
            session.close()


def delete_document(**kwargs):
    session = DBSession()
    try:

        document = (
            session.query(Document).filter(Document.id == kwargs["document_id"]).first()
        )
        if document:
            session.delete(document)
            session.commit()
    except:
        session.rollback()
        raise
    finally:
        if session:
            session.close()


def get_document(**kwargs) -> Document:
    session = DBSession()
    try:

        document = (
            session.query(Document)
            .filter(Document.uuid == kwargs["document_id"])
            .first()
        )
        return document
    except:
        session.rollback()
        raise
    finally:
        if session:
            session.close()


def get_documents(**kwargs) -> List[Document]:
    session = DBSession()
    try:

        documents = (
            session.query(Document)
            .filter(Document.base_uri == kwargs["base_uri"])
            .all()
        )
        return documents
    except:
        session.rollback()
        raise
    finally:
        if session:
            session.close()


_name_regex = re.compile(r"^[a-z0-9_-]{5,}$")


def is_valid_resource_name(name: str) -> bool:
    return name and _name_regex.match(name) is not None


def has_valid_keys(value: dict) -> bool:
    return (
        value is not None
        and isinstance(value, dict)
        and len(
            {
                key: val
                for key, val in value.items()
                if isblank(key) != 0 and isblank(value) != 0
            }
        )
        != 0
    )


def ingest_file(
    http_client: HttpClient, endpoint: str, file_path, metadata: dict
) -> Union[str, None]:
    response = http_client.upload(
        url=f"{endpoint}/v1/ingest/files",
        filepath=file_path,
        field="file",
        metadata=metadata,
    )

    return response


def un_ingest_file(http_client: HttpClient, endpoint: str, doc_id: str) -> None:
    http_client.delete(url=f"{endpoint}/v1/ingest/documents/{doc_id}")


def validate_schedule(schedule) -> BaseTrigger:
    try:
        # While apscheduler can make the conversion, we do it here to have full control of error behaviour
        if schedule is None:
            schedule_date = du.now()
        else:
            schedule_date = du.strptime(schedule)
        trigger = DateTrigger(run_date=schedule_date)
    except ValueError:
        schedule_date: Optional[du.dt.datetime] = None
        trigger: Optional[DateTrigger] = None

    if all([schedule_date, trigger]):
        if schedule is not None and schedule_date < du.now():
            raise ValueError("Schedule date has to be in the future")
        else:
            return trigger

    return CronTrigger.from_crontab(schedule)
