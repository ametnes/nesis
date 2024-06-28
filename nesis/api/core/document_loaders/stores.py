import json
import logging
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime
from sqlalchemy.orm import registry, Session

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
    class Document(object):
        def __init__(
            self,
            document_id,
            store_metadata,
            datasource_id,
            extract_metadata,
            last_modified,
        ):
            self.id = None
            self.document_id = document_id
            self.datasource_id = datasource_id
            self.extract_metadata = extract_metadata
            self.store_metadata = store_metadata
            self.last_modified = last_modified

    def __init__(self, url, table="extract", echo=False, pool_size=10):
        self._url = url
        self._engine = sa.create_engine(
            self._url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=pool_size,
        )

        mapper_registry = registry()

        self._table = sa.Table(
            table,
            mapper_registry.metadata,
            sa.Column("id", sa.BigInteger, autoincrement=True, primary_key=True),
            sa.Column("document_id", sa.Unicode(255), nullable=False, unique=True),
            sa.Column("datasource_id", sa.Unicode(255), nullable=False),
            sa.Column("extract_metadata", sa.JSON, nullable=False),
            sa.Column("store_metadata", sa.JSON, nullable=False),
            sa.Column(
                "last_modified", DateTime, default=datetime.utcnow, nullable=False
            ),
        )

        try:
            mapper_registry.map_imperatively(SqlDocumentStore.Document, self._table)
        except sa.exc.ArgumentError:
            # Table is already mapped
            pass
        mapper_registry.metadata.create_all(self._engine)

    def get(self, document_id) -> Document:
        with Session(self._engine) as session:
            return (
                session.query(SqlDocumentStore.Document)
                .filter(SqlDocumentStore.Document.document_id == document_id)
                .first()
            )

    def save(self, **kwargs) -> Document:
        with Session(self._engine) as session:
            session.expire_on_commit = False
            store_record = SqlDocumentStore.Document(
                document_id=kwargs["document_id"],
                datasource_id=kwargs["datasource_id"],
                extract_metadata=kwargs["extract_metadata"],
                store_metadata=kwargs["store_metadata"],
                last_modified=kwargs["last_modified"],
            )
            session.add(store_record)
            session.commit()

            return store_record

    def delete(self, document_id):
        with Session(self._engine) as session:
            store_record = (
                session.query(SqlDocumentStore.Document)
                .filter(SqlDocumentStore.Document.document_id == document_id)
                .first()
            )
            session.delete(store_record)
            session.commit()
