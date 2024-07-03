import json
import logging
import datetime as dt
import os
import uuid

import sqlalchemy as sa
from sqlalchemy import (
    Column,
    UniqueConstraint,
    Index,
    BigInteger,
    Unicode,
    JSON,
    DateTime,
    Text,
    Enum,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, declarative_base

from nesis.api.core.models import objects

_LOG = logging.getLogger(__name__)


class RagDocumentStore(object):
    def __init__(self, config, http_client):
        self._config = config
        self._http_client = http_client
        self._endpoint = (self._config.get("rag") or {}).get("endpoint")

    def save(self, **kwargs):
        metadata = kwargs["metadata"]
        text = kwargs["text"]
        file_name = kwargs["file_name"]
        url = f"{self._endpoint}/v1/ingest/texts"
        response = self._http_client.post(
            url=url,
            headers={"Content-Type": "application/json"},
            payload=json.dumps(
                {"metadata": metadata, "text": text, "file_name": file_name}
            ),
        )
        return json.loads(response)

    def delete(self, **kwargs):
        doc_id = kwargs["doc_id"]
        self._http_client.delete()


class SqlDocumentStore(object):

    def __init__(self, url, echo=False, pool_size=10):
        self._url = url
        self._engine = sa.create_engine(
            self._url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=pool_size,
        )

        Base = declarative_base()

        """
        1. Create a dynamic class/type so as to allow for multiple database connections.
        For example, we can extract data to a SQL Server or Postgres instance and avoid the class already mapped exception
        
        2. We use JSON database to allow for other database
        """
        self.Store = type(
            f"Store{str(uuid.uuid4()).split('-')[0]}",
            (Base,),
            {
                "__tablename__": "document_extract",
                "id": Column(BigInteger, primary_key=True, autoincrement=True),
                "uuid": Column(Unicode(255), nullable=False),
                "base_uri": Column(Unicode(4000), nullable=False),
                "filename": Column(Unicode(4000), nullable=False),
                "extract_metadata": Column(JSON),
                "datasource_id": Column(Unicode(255)),
                "store_metadata": Column(JSON),
                "status": Column(
                    Enum(objects.DocumentStatus, name="document_status"),
                    nullable=False,
                    default=objects.DocumentStatus.PROCESSING,
                ),
                "last_modified": Column(
                    DateTime, default=dt.datetime.utcnow, nullable=False
                ),
                "last_processed": Column(
                    DateTime, default=dt.datetime.utcnow, nullable=False
                ),
                "last_processed_message": Column(Text),
                "__table_args__": (
                    UniqueConstraint(
                        "uuid",
                        "datasource_id",
                        name="uq_document_extract_uuid_datasource_id",
                    ),
                    Index("idx_document_extract_base_uri", "base_uri"),
                ),
            },
        )

        try:
            Base.metadata.create_all(self._engine)
        except Exception as ex:
            ext_str = str(ex)
            if (
                "uq_document_extract_uuid_datasource_id" in ext_str
                or "idx_document_extract_base_uri" in ext_str
            ):
                # This would be an error about the index or unique key
                pass
            else:
                raise ex

    def get(self, **kwargs):
        document_id = kwargs.get("document_id")
        base_uri = kwargs.get("base_uri")
        with Session(self._engine) as session:
            query = session.query(self.Store)
            if document_id is not None:
                query = query.filter(self.Store.uuid == document_id)
            if base_uri is not None:
                query = query.filter(self.Store.base_uri == base_uri)

            return query.all()

    def save(self, **kwargs):
        with Session(self._engine) as session:
            session.expire_on_commit = False
            store_record = self.Store()

            store_record.uuid = kwargs["document_id"]
            store_record.datasource_id = kwargs["datasource_id"]
            store_record.extract_metadata = kwargs["extract_metadata"]
            store_record.store_metadata = kwargs["store_metadata"]
            store_record.last_modified = kwargs["last_modified"]
            store_record.base_uri = kwargs["base_uri"]
            store_record.rag_metadata = kwargs["rag_metadata"]
            store_record.filename = kwargs["filename"]

            session.add(store_record)
            session.commit()

            return store_record

    def delete(self, document_id):
        with Session(self._engine) as session:
            store_record = (
                session.query(self.Store).filter(self.Store.uuid == document_id).first()
            )
            session.delete(store_record)
            session.commit()
