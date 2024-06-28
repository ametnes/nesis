import json
import logging
from typing import Literal, Dict, Any

from fastapi import APIRouter, HTTPException, Request, UploadFile, Form
from pydantic import BaseModel, Field

from nesis.rag.core.server import ServiceException
from nesis.rag.core.server.extract.extract_service import ExtractService

extract_router = APIRouter(prefix="/v1")

_logger = logging.getLogger(__name__)


class ExtractResponse(BaseModel):
    object: Literal["list"]
    model: Literal["rag"]
    data: list[Dict[str, Any]]


@extract_router.post("/extractions/text", tags=["Extraction"])
def extract(request: Request, file: UploadFile) -> ExtractResponse:
    """Extract text from a file returning json elements that form that file."""

    service: ExtractService = request.state.injector.get(ExtractService)
    if file.filename is None:
        raise HTTPException(400, "No file name provided")

    try:
        ingested_documents = service.extract_bin(file.filename, file.file)
    except ServiceException as se:
        _logger.exception(f"Error ingesting file {file.filename}")
        raise HTTPException(400, str(se))
    return ExtractResponse(object="list", model="rag", data=ingested_documents)
