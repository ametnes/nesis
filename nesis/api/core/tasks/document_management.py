import os
from typing import List

import logging
import nesis.api.core.document_loaders.sharepoint as sharepoint_documents
from nesis.api.core.models.entities import Datasource, DatasourceType
from nesis.api.core.services.datasources import DatasourceService

import nesis.api.core.document_loaders.minio as s3_documents
import nesis.api.core.document_loaders.google_drive as google_drive
import nesis.api.core.document_loaders.samba as samba


_LOG = logging.getLogger(__name__)


def fetch_documents(**kwargs) -> None:
    try:
        config = kwargs["config"] or {}
        pgpt_endpoint = (config.get("llm") or {}).get("endpoint")
        http_client = kwargs["http_client"]
        datasource_list: List[Datasource] = DatasourceService.get_datasources()

        for datasource in datasource_list:
            if datasource.type == DatasourceType.MINIO:
                s3_documents.fetch_documents(
                    connection=datasource.connection,
                    pgpt_endpoint=pgpt_endpoint,
                    http_client=http_client,
                    metadata={"datasource": datasource.name},
                )
            if datasource.type == DatasourceType.SHAREPOINT:
                sharepoint_documents.fetch_documents(
                    **kwargs,
                    connection=datasource.connection,
                    pgpt_endpoint=pgpt_endpoint,
                    metadata={"datasource": datasource.name}
                )
            if datasource.type == DatasourceType.GOOGLE_DRIVE:
                google_drive.fetch_documents(
                    connection=datasource.connection,
                    llm_endpoint=pgpt_endpoint,
                    http_client=http_client,
                    metadata={"datasource": datasource.name},
                )
            if datasource.type == DatasourceType.WINDOWS_SHARE:
                samba.fetch_documents(
                    connection=datasource.connection,
                    llm_endpoint=pgpt_endpoint,
                    http_client=http_client,
                    metadata={"datasource": datasource.name},
                )
    except:
        _LOG.exception("Error fetching documents")
