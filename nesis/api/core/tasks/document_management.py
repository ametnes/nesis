import os
from typing import List

import logging
import nesis.api.core.document_loaders.sharepoint as sharepoint_documents
from nesis.api.core.models.entities import Datasource, DatasourceType
from nesis.api.core.services.datasources import DatasourceService

import nesis.api.core.document_loaders.minio as s3_documents
import nesis.api.core.document_loaders.google_drive as google_drive
import nesis.api.core.document_loaders.samba as samba
from nesis.api.core.util import http

_LOG = logging.getLogger(__name__)


def ingest_datasource(**kwargs) -> None:
    config = kwargs["config"] or {}
    http_client = kwargs.get("http_client")
    if http_client is None:
        http_client = http.HttpClient(config=config)
    params = kwargs["params"]

    datasource_param = params["datasource"]

    rag_endpoint = (config.get("rag") or {}).get("endpoint")
    datasource: Datasource = DatasourceService.get_datasource(
        datasource_id=datasource_param["id"]
    )

    match datasource.type:
        case DatasourceType.MINIO:
            s3_documents.fetch_documents(
                connection=datasource.connection,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
                metadata={"datasource": datasource.name},
            )
        case DatasourceType.SHAREPOINT:
            sharepoint_documents.fetch_documents(
                **kwargs,
                connection=datasource.connection,
                rag_endpoint=rag_endpoint,
                metadata={"datasource": datasource.name},
            )
        case DatasourceType.GOOGLE_DRIVE:
            google_drive.fetch_documents(
                connection=datasource.connection,
                llm_endpoint=rag_endpoint,
                http_client=http_client,
                metadata={"datasource": datasource.name},
            )
        case DatasourceType.WINDOWS_SHARE:
            samba.fetch_documents(
                connection=datasource.connection,
                llm_endpoint=rag_endpoint,
                http_client=http_client,
                metadata={"datasource": datasource.name},
            )
        case _:
            raise ValueError("Invalid datasource type")
