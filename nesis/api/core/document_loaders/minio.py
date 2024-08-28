import logging
import logging
import os
import tempfile
from typing import Dict, Any

import memcache
from minio import Minio

import nesis.api.core.util.http as http
from nesis.api.core.document_loaders.loader_helper import DocumentProcessor
from nesis.api.core.models.entities import Datasource
from nesis.api.core.util import clean_control, isblank
from nesis.api.core.util.concurrency import (
    IOBoundPool,
    as_completed,
)
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT

_LOG = logging.getLogger(__name__)


class MinioProcessor(DocumentProcessor):
    def __init__(
        self,
        config,
        http_client: http.HttpClient,
        cache_client: memcache.Client,
        datasource: Datasource,
    ):
        super().__init__(config, http_client, datasource)
        self._config = config
        self._http_client = http_client
        self._cache_client = cache_client
        self._datasource = datasource

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
            futures = []

            for bucket_name in bucket_names_parts:
                try:
                    bucket_objects = client.list_objects(bucket_name, recursive=True)
                except:
                    _LOG.warning(f"Failed to list objects in bucket {bucket_name}")
                    continue

                for bucket_object in bucket_objects:
                    futures.append(
                        IOBoundPool.submit(
                            self._process_object,
                            bucket_name,
                            client,
                            datasource,
                            bucket_object,
                            metadata,
                        )
                    )
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    _LOG.warning(future.exception())
        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)

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
                f"Starting {self._mode}ing object {item.object_name} in bucket {bucket_name}"
            )
            file_path = f"{tmp_file.name}-{item.object_name}"

            # Write item to file
            client.fget_object(
                bucket_name=bucket_name,
                object_name=item.object_name,
                file_path=file_path,
            )

            self.sync(
                endpoint,
                file_path,
                item.last_modified,
                metadata,
                store_metadata={
                    "bucket_name": item.bucket_name,
                    "object_name": item.object_name,
                    "filename": item.object_name,
                    "size": item.size,
                    "last_modified": item.last_modified.strftime(
                        DEFAULT_DATETIME_FORMAT
                    ),
                    "version_id": item.version_id,
                },
            )

            _LOG.info(
                f"Done {self._mode}ing object {item.object_name} in bucket {bucket_name}"
            )
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
    ) -> None:

        def clean(**kwargs):
            store_metadata = kwargs["store_metadata"]
            try:
                client.stat_object(
                    bucket_name=store_metadata["bucket_name"],
                    object_name=store_metadata["object_name"],
                )
                return False
            except Exception as ex:
                str_ex = str(ex)
                if "NoSuchKey" in str_ex and "does not exist" in str_ex:
                    return True
                else:
                    raise

        try:
            self.unsync(clean=clean)
        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)


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
