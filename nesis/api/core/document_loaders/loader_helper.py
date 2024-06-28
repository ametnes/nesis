import json
import logging

from nesis.api.core.models.entities import Document
from nesis.api.core.services.util import get_document, delete_document
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


def upload_document_to_llm(upload_document, file_metadata, rag_endpoint, http_client):
    return _upload_document_to_pgpt(
        upload_document, file_metadata, rag_endpoint, http_client
    )


def _upload_document_to_pgpt(upload_document, file_metadata, rag_endpoint, http_client):
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
                    http_client.delete()
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
