import datetime
import json
import logging
import uuid
from typing import Optional, Dict, Any, Callable

import nesis.api.core.util.http as http
from nesis.api.core.document_loaders.runners import (
    IngestRunner,
    ExtractRunner,
    RagRunner,
)
from nesis.api.core.models.entities import Document, Datasource
from nesis.api.core.services.util import delete_document
from nesis.api.core.services.util import (
    get_document,
)
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


def upload_document_to_llm(upload_document, file_metadata, rag_endpoint, http_client):
    return _upload_document(upload_document, file_metadata, rag_endpoint, http_client)


def _upload_document(upload_document, file_metadata, rag_endpoint, http_client):
    document_id = file_metadata["unique_id"]
    file_name = file_metadata["name"]

    db_document: Document = get_document(document_id=document_id)

    if db_document:
        store_metadata = db_document.store_metadata
        if store_metadata and store_metadata.get("last_modified"):
            if not strptime(date_string=store_metadata["last_modified"]).replace(
                tzinfo=None
            ) < file_metadata["last_modified"].replace(tzinfo=None).replace(
                microsecond=0
            ):
                _LOG.debug(f"Skipping file {file_metadata['name']} already up to date")
                return None
            rag_metadata: dict = db_document.rag_metadata
            if rag_metadata is None:
                return None
            for document_data in rag_metadata.get("data") or []:
                try:
                    http_client.delete(
                        url=f"{rag_endpoint}/v1/ingest/{document_data['doc_id']}"
                    )
                except:
                    _LOG.warn(f"Failed to delete document {document_data['doc_id']}")

            try:
                delete_document(document_id=document_id)
            except:
                _LOG.warn(
                    f"Failed to delete file {file_name}'s record. Continuing anyway..."
                )

    request_object = {"file_name": file_name, "text": upload_document.page_content}
    response = http_client.post(url=f"{rag_endpoint}/v1/ingest", payload=request_object)
    return json.loads(response)


class DocumentProcessor(object):
    def __init__(
        self,
        config,
        http_client: http.HttpClient,
        datasource: Datasource,
    ):
        self._datasource = datasource

        # This is left package public for testing
        self._extract_runner: ExtractRunner = Optional[None]
        _ingest_runner = IngestRunner(config=config, http_client=http_client)

        if self._datasource.connection.get("destination") is not None:
            self._extract_runner = ExtractRunner(
                config=config,
                http_client=http_client,
                destination=self._datasource.connection.get("destination"),
            )

        self._mode = self._datasource.connection.get("mode") or "ingest"

        match self._mode:
            case "ingest":
                self._ingest_runners: list[RagRunner] = [_ingest_runner]
            case "extract":
                self._ingest_runners: list[RagRunner] = [self._extract_runner]
            case _:
                raise ValueError(
                    f"Invalid mode {self._mode}. Expected 'ingest' or 'extract'"
                )

    def sync(
        self,
        endpoint: str,
        file_path: str,
        last_modified: datetime.datetime,
        metadata: Dict[str, Any],
        store_metadata: Dict[str, Any],
    ) -> None:
        """
        Here we check if this file has been updated.
        If the file has been updated, we delete it from the vector store and re-ingest the new updated file
        """
        document_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS, f"{self._datasource.uuid}:{metadata['self_link']}"
            )
        )
        document: Document = get_document(document_id=document_id)
        for _ingest_runner in self._ingest_runners:
            try:
                response_json = _ingest_runner.run(
                    file_path=file_path,
                    metadata=metadata,
                    document_id=None if document is None else document.uuid,
                    last_modified=last_modified.replace(tzinfo=None).replace(
                        microsecond=0
                    ),
                    datasource=self._datasource,
                )
            except ValueError:
                _LOG.warning(f"File {file_path} ingestion failed", exc_info=True)
                response_json = None
            except UserWarning:
                _LOG.warning(f"File {file_path} is already processing")
                continue

            if response_json is None:
                _LOG.warning("No response from ingest runner received")
                continue

            _ingest_runner.save(
                document_id=document_id,
                datasource_id=self._datasource.uuid,
                filename=store_metadata["filename"],
                base_uri=endpoint,
                rag_metadata=response_json,
                store_metadata=store_metadata,
                last_modified=last_modified,
            )

    def unsync(self, clean: Callable) -> None:
        endpoint = self._datasource.connection.get("endpoint")

        for _ingest_runner in self._ingest_runners:
            documents = _ingest_runner.get(base_uri=endpoint)
            for document in documents:
                store_metadata = document.store_metadata
                try:
                    rag_metadata = document.rag_metadata
                except AttributeError:
                    rag_metadata = document.extract_metadata

                if clean(store_metadata=store_metadata):
                    _ingest_runner.delete(document=document, rag_metadata=rag_metadata)
