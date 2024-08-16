import logging

import memcache

import nesis.api.core.document_loaders.google_drive as google_drive
import nesis.api.core.document_loaders.minio as minio
import nesis.api.core.document_loaders.s3 as s3
import nesis.api.core.document_loaders.samba as samba
import nesis.api.core.document_loaders.sharepoint as sharepoint
from nesis.api.core.models.entities import Datasource
from nesis.api.core.models.objects import DatasourceType
from nesis.api.core.services.datasources import DatasourceService
from nesis.api.core.util import http

_LOG = logging.getLogger(__name__)


def ingest_datasource(**kwargs) -> None:
    config = kwargs["config"] or {}
    http_client = kwargs.get("http_client")
    if http_client is None:
        http_client = http.HttpClient(config=config)
    cache_client = kwargs.get("cache_client")
    if cache_client is None:
        cache_client = memcache.Client(config["memcache"]["hosts"], debug=1)
    params = kwargs["params"]

    datasource_param = params["datasource"]

    rag_endpoint = (config.get("rag") or {}).get("endpoint")
    datasource: Datasource = DatasourceService.get_datasource(
        datasource_id=datasource_param["id"]
    )

    if datasource is None:
        _LOG.warning(f"Datasource {datasource_param['id']} not found")
        raise ValueError(f'Invalid datasource {datasource_param["id"]}')

    metadata = {"datasource": datasource.name}

    match datasource.type:
        case DatasourceType.MINIO:

            minio_ingestor = minio.MinioProcessor(
                config=config,
                http_client=http_client,
                cache_client=cache_client,
                datasource=datasource,
            )

            minio_ingestor.run(metadata=metadata)

        case DatasourceType.SHAREPOINT:
            sharepoint.fetch_documents(
                datasource=datasource,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
                cache_client=cache_client,
                metadata={"datasource": datasource.name},
            )
        case DatasourceType.WINDOWS_SHARE:
            samba.fetch_documents(
                connection=datasource.connection,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
                metadata={"datasource": datasource.name},
                cache_client=cache_client,
            )
        case DatasourceType.S3:
            minio_ingestor = s3.Processor(
                config=config,
                http_client=http_client,
                cache_client=cache_client,
                datasource=datasource,
            )

            minio_ingestor.run(metadata=metadata)

        case _:
            raise ValueError("Invalid datasource type")
