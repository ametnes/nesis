import json
import logging

import sqlalchemy as sa
from sqlalchemy.orm import registry, Session

from nesis.api.core.models.entities import Document, DocumentObject

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

        mapper_registry = registry()

        try:
            mapper_registry.map_declaratively(DocumentObject)

        except sa.exc.ArgumentError as ex:
            # Table is already mapped
            _LOG.warning("Error mapping store", exc_info=True)
            pass
        mapper_registry.metadata.create_all(self._engine)

    def get(self, document_id) -> DocumentObject:
        with Session(self._engine) as session:
            return (
                session.query(DocumentObject)
                .filter(DocumentObject.uuid == document_id)
                .first()
            )

    def save(self, **kwargs) -> DocumentObject:
        with Session(self._engine) as session:
            session.expire_on_commit = False
            store_record = Document(
                document_id=kwargs["document_id"],
                datasource_id=kwargs["datasource_id"],
                extract_metadata=kwargs["extract_metadata"],
                store_metadata=kwargs["store_metadata"],
                last_modified=kwargs["last_modified"],
                base_uri=kwargs["base_uri"],
                rag_metadata=kwargs["rag_metadata"],
                filename=kwargs["filename"],
            )
            session.add(store_record)
            session.commit()

            return store_record

    def delete(self, document_id):
        with Session(self._engine) as session:
            store_record = (
                session.query(DocumentObject)
                .filter(DocumentObject.document_id == document_id)
                .first()
            )
            session.delete(store_record)
            session.commit()
