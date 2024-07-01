import logging
import os
import tempfile
from typing import Dict, Any

import memcache
import minio
from minio import Minio

import nesis.api.core.util.http as http
from nesis.api.core.document_loaders.runners import (
    IngestRunner,
    ExtractRunner,
    RagRunner,
)
from nesis.api.core.models.entities import Document, Datasource
from nesis.api.core.services.util import (
    get_document,
    get_documents,
)
from nesis.api.core.util import clean_control, isblank
from nesis.api.core.util.concurrency import IOBoundPool, as_completed
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT

_LOG = logging.getLogger(__name__)


class MinioProcessor(object):
    def __init__(
        self,
        config,
        http_client: http.HttpClient,
        cache_client: memcache.Client,
        datasource: Datasource,
    ):
        self._config = config
        self._http_client = http_client
        self._cache_client = cache_client
        self._datasource = datasource

        _extract_runner = None
        _ingest_runner = IngestRunner(config=config, http_client=http_client)
        if self._datasource.connection.get("destination") is not None:
            _extract_runner = ExtractRunner(
                config=config,
                http_client=http_client,
                destination=self._datasource.connection.get("destination"),
            )
        self._ingest_runners = []

        self._ingest_runners = [IngestRunner(config=config, http_client=http_client)]

        mode = self._datasource.connection.get("mode") or "ingest"

        match mode:
            case "ingest":
                self._ingest_runners: list[RagRunner] = [_ingest_runner]
            case "extract":
                self._ingest_runners: list[RagRunner] = [_extract_runner]
            case _:
                raise ValueError(f"Invalid mode {mode}. Expected 'ingest' or 'extract'")

    def run(self, metadata: Dict[str, Any]):
        connection: Dict[str, str] = self._datasource.connection
        try:
            endpoint = connection.get("endpoint")
            access_key = connection.get("user")
            secret_key = connection.get("password")

            endpoint_parts = endpoint.split("://")
            _minio_client = Minio(
                endpoint=endpoint_parts[1].split("/")[0],
                access_key=access_key,
                secret_key=secret_key,
                secure=endpoint_parts[0] == "https",
            )

            self._sync_documents(
                client=_minio_client,
                datasource=self._datasource,
                metadata=metadata,
            )
            self._unsync_documents(
                client=_minio_client,
                connection=connection,
            )
        except:
            _LOG.exception("Error fetching sharepoint documents")

    def _sync_documents(
        self,
        client: Minio,
        datasource: Datasource,
        metadata: dict,
    ) -> None:

        try:

            connection = datasource.connection
            # Data objects allow us to specify bucket names
            bucket_names = connection.get("dataobjects")

            bucket_names_parts = bucket_names.split(",")

            for bucket_name in bucket_names_parts:
                try:
                    bucket_objects = client.list_objects(bucket_name, recursive=True)
                except:
                    _LOG.warning(f"Failed to list objects in bucket {bucket_name}")
                    continue

                bucket_objects_list = []
                batch_size = 5
                for item in bucket_objects:
                    bucket_objects_list.append(item)
                    if len(bucket_objects_list) < batch_size:
                        continue
                    self._process_objects(
                        bucket_name, bucket_objects_list, client, datasource, metadata
                    )
                    bucket_objects_list = []

                # Process the remaining objects, if any
                self._process_objects(
                    bucket_name, bucket_objects_list, client, datasource, metadata
                )

        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)

    def _process_objects(
        self, bucket_name, bucket_objects_list, client, datasource, metadata
    ):
        futures = [
            IOBoundPool.submit(
                self._process_object,
                bucket_name,
                client,
                datasource,
                bucket_objects_list_item,
                metadata,
            )
            for bucket_objects_list_item in bucket_objects_list
        ]
        for future in as_completed(futures):
            try:
                future.result()
            except:
                _LOG.warning(future.exception())

    def _process_object(self, bucket_name, client, datasource, item, metadata):
        connection = datasource.connection
        endpoint = connection["endpoint"]
        self_link = f"{endpoint}/{bucket_name}/{item.object_name}"
        _metadata = {
            **(metadata or {}),
            "file_name": f"{bucket_name}/{item.object_name}",
            "self_link": self_link,
        }
        """
                        We use memcache's add functionality to implement a shared lock to allow for multiple instances
                        operating 
                        """
        _lock_key = clean_control(f"{__name__}/locks/{self_link}")
        if self._cache_client.add(key=_lock_key, val=_lock_key, time=30 * 60):
            try:
                self._sync_document(
                    client=client,
                    datasource=datasource,
                    metadata=_metadata,
                    bucket_name=bucket_name,
                    item=item,
                )
            finally:
                self._cache_client.delete(_lock_key)
        else:
            _LOG.info(f"Document {self_link} is already processing")

    def _sync_document(
        self,
        client: Minio,
        datasource: Datasource,
        metadata: dict,
        bucket_name: str,
        item,
    ):
        connection = datasource.connection
        endpoint = connection["endpoint"]
        _metadata = metadata
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            _LOG.info(
                f"Starting syncing object {item.object_name} in bucket {bucket_name}"
            )
            file_path = f"{tmp_file.name}-{item.object_name}"

            # Write item to file
            client.fget_object(
                bucket_name=bucket_name,
                object_name=item.object_name,
                file_path=file_path,
            )

            """
            Here we check if this file has been updated.
            If the file has been updated, we delete it from the vector store and re-ingest the new updated file
            """
            document: Document = get_document(document_id=item.etag)
            document_id = None if document is None else document.uuid

            for _ingest_runner in self._ingest_runners:

                try:
                    response_json = _ingest_runner.run(
                        file_path=file_path,
                        metadata=metadata,
                        document_id=document_id,
                        last_modified=item.last_modified.replace(tzinfo=None).replace(
                            microsecond=0
                        ),
                        datasource=datasource,
                    )
                except ValueError:
                    _LOG.warning(f"File {file_path} ingestion failed", exc_info=True)
                    response_json = {}
                except UserWarning:
                    _LOG.debug(f"File {file_path} is already processing")
                    return

                _ingest_runner.save(
                    document_id=item.etag,
                    datasource_id=datasource.uuid,
                    filename=item.object_name,
                    base_uri=endpoint,
                    rag_metadata=response_json,
                    store_metadata={
                        "bucket_name": item.bucket_name,
                        "object_name": item.object_name,
                        "etag": item.etag,
                        "size": item.size,
                        "last_modified": item.last_modified.strftime(
                            DEFAULT_DATETIME_FORMAT
                        ),
                        "version_id": item.version_id,
                    },
                    last_modified=item.last_modified,
                )

            _LOG.info(f"Done syncing object {item.object_name} in bucket {bucket_name}")
        except Exception as ex:
            _LOG.warning(
                f"Error when getting and ingesting document {item.object_name} - {ex}",
                exc_info=True,
            )
        finally:
            tmp_file.close()
            os.unlink(tmp_file.name)

    def _unsync_documents(
        self,
        client: Minio,
        connection: dict,
    ) -> None:

        try:
            endpoint = connection.get("endpoint")

            documents = get_documents(base_uri=endpoint)
            for document in documents:
                store_metadata = document.store_metadata
                rag_metadata = document.rag_metadata
                bucket_name = store_metadata["bucket_name"]
                object_name = store_metadata["object_name"]
                try:
                    client.stat_object(bucket_name=bucket_name, object_name=object_name)
                except minio.error.S3Error as ex:
                    str_ex = str(ex)
                    if "NoSuchKey" in str_ex and "does not exist" in str_ex:
                        for _ingest_runner in self._ingest_runners:
                            _ingest_runner.delete(
                                document=document, rag_metadata=rag_metadata
                            )
                    else:
                        raise

        except:
            _LOG.warn("Error fetching and updating documents", exc_info=True)


def validate_connection_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    _valid_keys = ["endpoint", "user", "password", "dataobjects", "destination", "mode"]
    assert not isblank(connection.get("endpoint")), "An endpoint must be supplied"
    assert not isblank(
        connection.get("dataobjects")
    ), "One or more buckets must be supplied"
    return {
        key: val
        for key, val in connection.items()
        if key in _valid_keys and not isblank(connection[key])
    }
