import json
import logging
from typing import Literal


from fastapi import APIRouter, HTTPException, Request, UploadFile, Form
from pydantic import BaseModel, Field

from nesis.rag.core.server import ServiceException
from nesis.rag.core.server.ingest.ingest_service import IngestService
from nesis.rag.core.server.ingest.model import IngestedDoc

ingest_router = APIRouter(prefix="/v1")

_logger = logging.getLogger(__name__)


class IngestTextBody(BaseModel):
    file_name: str = Field(examples=["Avatar: The Last Airbender"])
    text: str = Field(
        examples=[
            "Avatar is set in an Asian and Arctic-inspired world in which some "
            "people can telekinetically manipulate one of the four elements—water, "
            "earth, fire or air—through practices known as 'bending', inspired by "
            "Chinese martial arts."
        ]
    )


class IngestResponse(BaseModel):
    object: Literal["list"]
    model: Literal["rag"]
    data: list[IngestedDoc]


@ingest_router.post("/ingest/files", tags=["Ingestion"])
def ingest_file(
    request: Request, file: UploadFile, metadata: str = Form(...)
) -> IngestResponse:
    """Ingests and processes a file, storing its chunks to be used as context.

    The context obtained from files is later used in
    `/chat/completions`, `/completions`, and `/chunks` APIs.

    Most common document
    formats are supported, but you may be prompted to install an extra dependency to
    manage a specific file type.

    A file can generate different Documents (for example a PDF generates one Document
    per page). All Documents IDs are returned in the response, together with the
    extracted Metadata (which is later used to improve context retrieval). Those IDs
    can be used to filter the context used to create responses in
    `/chat/completions`, `/completions`, and `/chunks` APIs.
    """

    service = request.state.injector.get(IngestService)
    if file.filename is None:
        raise HTTPException(400, "No file name provided")
    try:
        _metadata_str = request.query_params.get("metadata") or str(metadata)
        _metadata = json.loads(_metadata_str)
    except ValueError:
        error = "Invalid of missing metadata field"
        _logger.exception(error)
        raise HTTPException(400, error)
    try:
        ingested_documents = service.ingest_bin_data(
            file.filename, file.file, metadata=_metadata
        )
    except ServiceException as se:
        _logger.exception(f"Error ingesting file {file.filename}")
        raise HTTPException(400, str(se))
    return IngestResponse(object="list", model="rag", data=ingested_documents)


@ingest_router.post("/ingest/texts", tags=["Ingestion"])
def ingest_text(request: Request, body: IngestTextBody) -> IngestResponse:
    """Ingests and processes a text, storing its chunks to be used as context.

    The context obtained from files is later used in
    `/chat/completions`, `/completions`, and `/chunks` APIs.

    A Document will be generated with the given text. The Document
    ID is returned in the response, together with the
    extracted Metadata (which is later used to improve context retrieval). That ID
    can be used to filter the context used to create responses in
    `/chat/completions`, `/completions`, and `/chunks` APIs.
    """
    service = request.state.injector.get(IngestService)
    if len(body.file_name) == 0:
        raise HTTPException(400, "No file name provided")
    ingested_documents = service.ingest_text(body.file_name, body.text)
    return IngestResponse(object="list", model="rag", data=ingested_documents)


@ingest_router.get("/ingest/files", tags=["Ingestion"])
def list_ingested(request: Request) -> IngestResponse:
    """Lists already ingested Documents including their Document ID and metadata.

    Those IDs can be used to filter the context used to create responses
    in `/chat/completions`, `/completions`, and `/chunks` APIs.
    """
    service = request.state.injector.get(IngestService)
    ingested_documents = service.list_ingested()
    return IngestResponse(object="list", model="rag", data=ingested_documents)


@ingest_router.delete("/ingest/documents/{doc_id}", tags=["Ingestion"])
def delete_ingested(request: Request, doc_id: str) -> None:
    """Delete the specified ingested Document.

    The `doc_id` can be obtained from the `GET /ingest/list` endpoint.
    The document will be effectively deleted from your storage context.
    """
    service = request.state.injector.get(IngestService)
    service.delete(doc_id)
