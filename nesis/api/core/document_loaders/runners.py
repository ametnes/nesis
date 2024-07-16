import abc
import datetime
import json
import logging
from typing import Dict, Any, Union

import nesis.api.core.util.http as http
from nesis.api.core.document_loaders.stores import SqlDocumentStore
from nesis.api.core.models.entities import Document, Datasource
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
)
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


class RagRunner(abc.ABC):
    @abc.abstractmethod
    def run(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: str,
        datasource: Datasource,
        last_modified: datetime.datetime,
        **kwargs,
    ) -> Union[Dict[str, Any], None]:
        pass

    @abc.abstractmethod
    def save(self, **kwargs) -> Document:
        pass

    @abc.abstractmethod
    def delete(self, document: Document, **kwargs) -> None:
        pass

    @abc.abstractmethod
    def get(self, **kwargs) -> list:
        pass


class ExtractRunner(RagRunner):

    def __init__(
        self,
        config: Dict[str, Any],
        destination: Dict[str, Any],
        http_client: http.HttpClient,
    ):
        self._config = config
        self._http_client = http_client
        self._endpoint = self._config

        if destination is None:
            raise ValueError("Destination for the extraction is missing")
        _sql_extraction_store = destination["sql"]

        self._extraction_store = SqlDocumentStore(**_sql_extraction_store)
        self._rag_endpoint = (self._config.get("rag") or {}).get("endpoint")

    def run(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: str,
        datasource: Datasource,
        last_modified: datetime.datetime,
        **kwargs,
    ) -> Union[Dict[str, Any], None]:

        if document_id is not None:
            _is_modified = self._is_modified(
                document_id=document_id, last_modified=last_modified
            )
            if _is_modified is None or not _is_modified:
                return

        url = f"{self._rag_endpoint}/v1/extractions/text"

        response = self._http_client.upload(
            url=url,
            filepath=file_path,
            field="file",
            metadata=metadata,
        )
        return json.loads(response)

    def get(self, **kwargs) -> list:
        return self._extraction_store.get(base_uri=kwargs.get("base_uri"))

    def _is_modified(
        self, document_id, last_modified: datetime.datetime
    ) -> Union[bool, None]:
        """
        Here we check if this file has been updated.
        If the file has been updated, we delete it from the vector store and re-ingest the new updated file
        """
        documents = self._extraction_store.get(document_id=document_id)
        for document in documents:
            if document is not None and last_modified.replace(
                microsecond=0
            ) > document.last_modified.replace(microsecond=0):
                try:
                    self.delete(document=document)
                except:
                    _LOG.warning(
                        f"Failed to delete document {document_id}'s record. Continuing anyway..."
                    )
                return True
            return False

    def save(self, **kwargs):
        return self._extraction_store.save(
            document_id=kwargs["document_id"],
            datasource_id=kwargs["datasource_id"],
            extract_metadata=kwargs["rag_metadata"],
            store_metadata=kwargs["store_metadata"],
            last_modified=kwargs["last_modified"],
            base_uri=kwargs["base_uri"],
            rag_metadata=kwargs["rag_metadata"],
            filename=kwargs["filename"],
        )

    def delete(self, document, **kwargs) -> None:
        self._extraction_store.delete(document_id=document.uuid)


class IngestRunner(RagRunner):

    def get(self, **kwargs) -> list:
        base_uri = kwargs.get("base_uri")
        return get_documents(base_uri=base_uri)

    def __init__(self, config, http_client):
        self._config = config
        self._http_client: http.HttpClient = http_client
        self._endpoint = self._config

        self._rag_endpoint = (self._config.get("rag") or {}).get("endpoint")

    def run(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: str,
        datasource: Datasource,
        last_modified: datetime.datetime,
        **kwargs,
    ) -> Union[Dict[str, Any], None]:

        if document_id is not None:
            _is_modified = self._is_modified(
                document_id=document_id,
                datasource=datasource,
                last_modified=last_modified,
            )
            if _is_modified is None or not _is_modified:
                return

        url = f"{self._rag_endpoint}/v1/ingest/files"

        response = self._http_client.upload(
            url=url,
            filepath=file_path,
            field="file",
            metadata=metadata,
        )
        return json.loads(response)

    def _is_modified(
        self, document_id, datasource: Datasource, last_modified: datetime.datetime
    ) -> Union[bool, None]:
        """
        Here we check if this file has been updated.
        If the file has been updated, we delete it from the vector store and re-ingest the new updated file
        """
        endpoint = datasource.connection["endpoint"]
        document: Document = get_document(document_id=document_id)
        if document is None or document.base_uri != endpoint:
            return False
        elif document.base_uri == endpoint:
            store_metadata = document.store_metadata
            document_last_modified = document.last_modified
            if (
                document_last_modified is None
                and store_metadata
                and store_metadata.get("last_modified")
            ):
                document_last_modified = strptime(
                    date_string=store_metadata["last_modified"]
                ).replace(tzinfo=None)
            if document_last_modified is not None and last_modified.replace(
                microsecond=0
            ) > document_last_modified.replace(microsecond=0):
                try:
                    self.delete(document=document, rag_metadata=document.rag_metadata)
                except:
                    _LOG.warning(
                        f"Failed to delete document {document_id}'s record. Continuing anyway...",
                        exc_info=True,
                    )
                return True
            return False
        else:
            return None

    def save(self, **kwargs) -> Document:
        return save_document(
            document_id=kwargs["document_id"],
            filename=kwargs["filename"],
            base_uri=kwargs["base_uri"],
            rag_metadata=kwargs["rag_metadata"],
            store_metadata=kwargs["store_metadata"],
            last_modified=kwargs["last_modified"],
            datasource_id=kwargs["datasource_id"],
        )

    def delete(self, document: Document, **kwargs) -> None:
        endpoint = (self._config.get("rag") or {}).get("endpoint")
        rag_metadata = kwargs["rag_metadata"]

        try:
            self._http_client.deletes(
                urls=[
                    f"{endpoint}/v1/ingest/documents/{document_data['doc_id']}"
                    for document_data in rag_metadata.get("data") or []
                ]
            )
            _LOG.info(f"Deleting document {document.filename}")
            delete_document(document_id=document.id)
        except:
            _LOG.warning(
                f"Failed to delete document {document.filename}",
                exc_info=True,
            )
