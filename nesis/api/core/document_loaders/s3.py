import json
import logging
import pathlib
import tempfile
from concurrent.futures import as_completed
from typing import Dict, Any

import boto3
import memcache

import nesis.api.core.util.http as http
from nesis.api.core.document_loaders.loader_helper import DocumentProcessor
from nesis.api.core.models.entities import Document, Datasource
from nesis.api.core.services import util
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
    ingest_file,
)
from nesis.api.core.util import clean_control, isblank
from nesis.api.core.util.concurrency import IOBoundPool
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


class Processor(DocumentProcessor):
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
            region = connection.get("region")
            if all([access_key, secret_key]):
                if endpoint:
                    s3_client = boto3.client(
                        "s3",
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=region,
                        endpoint_url=endpoint,
                    )
                else:
                    s3_client = boto3.client(
                        "s3",
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=region,
                    )
            else:
                if endpoint:
                    s3_client = boto3.client(
                        "s3", region_name=region, endpoint_url=endpoint
                    )
                else:
                    s3_client = boto3.client("s3", region_name=region)

            self._sync_documents(
                client=s3_client,
                datasource=self._datasource,
                metadata=metadata,
            )
            self._unsync_documents(
                client=s3_client,
            )
        except:
            _LOG.exception("Error fetching sharepoint documents")

    def _sync_documents(
        self,
        client,
        datasource: Datasource,
        metadata: dict,
    ) -> None:

        try:

            # Data objects allow us to specify bucket names
            connection = datasource.connection
            bucket_paths = connection.get("dataobjects")
            if bucket_paths is None:
                _LOG.warning("No bucket names supplied, so I can't do much")

            bucket_paths_parts = bucket_paths.split(",")
            futures = []
            for bucket_path in bucket_paths_parts:

                # a/b/c/// should only give [a,b,c]
                bucket_path_parts = [
                    part for part in bucket_path.split("/") if len(part) != 0
                ]

                path = "/".join(bucket_path_parts[1:])
                bucket_name = bucket_path_parts[0]

                paginator = client.get_paginator("list_objects_v2")
                page_iterator = paginator.paginate(
                    Bucket=bucket_name,
                    Prefix="" if path == "" else f"{path}/",
                )
                for result in page_iterator:
                    if result["KeyCount"] == 0:
                        continue
                    # iterate through files
                    for item in result["Contents"]:
                        # Paths ending in / are folders so we skip them
                        if item["Key"].endswith("/"):
                            continue
                        futures.append(
                            IOBoundPool.submit(
                                self._process_object,
                                bucket_name,
                                client,
                                datasource,
                                item,
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
        self_link = f"{endpoint}/{bucket_name}/{item['Key']}"
        _metadata = {
            **(metadata or {}),
            "file_name": f"{bucket_name}/{item['Key']}",
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
        client,
        datasource: Datasource,
        metadata: dict,
        bucket_name: str,
        item,
    ):
        endpoint = datasource.connection["endpoint"]
        _metadata = metadata

        with tempfile.NamedTemporaryFile(
            dir=tempfile.gettempdir(),
        ) as tmp:
            key_parts = item["Key"].split("/")

            path_to_tmp = f"{str(pathlib.Path(tmp.name).absolute())}-{key_parts[-1]}"

            try:
                _LOG.info(
                    f"Starting syncing object {item['Key']} in bucket {bucket_name}"
                )
                # Write item to file
                client.download_file(bucket_name, item["Key"], path_to_tmp)
                self.sync(
                    endpoint,
                    path_to_tmp,
                    last_modified=item["LastModified"],
                    metadata=metadata,
                    store_metadata={
                        "bucket_name": bucket_name,
                        "object_name": item["Key"],
                        "filename": item["Key"],
                        "size": item["Size"],
                        "last_modified": item["LastModified"].strftime(
                            DEFAULT_DATETIME_FORMAT
                        ),
                    },
                )

                _LOG.info(f"Done syncing object {item['Key']} in bucket {bucket_name}")
            except:
                _LOG.warning(
                    f"Error when getting and ingesting document {item['Key']}",
                    exc_info=True,
                )

    def _unsync_documents(self, client) -> None:
        def clean(**kwargs):
            store_metadata = kwargs["store_metadata"]
            try:
                client.head_object(
                    Bucket=store_metadata["bucket_name"],
                    Key=store_metadata["object_name"],
                )
                return False
            except Exception as ex:
                str_ex = str(ex)
                if not ("object" in str_ex and "not found" in str_ex):
                    return True
                else:
                    raise

        try:
            self.unsync(clean=clean)
        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)


def validate_connection_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    _valid_keys = ["endpoint", "user", "password", "region", "dataobjects"]
    assert not isblank(connection.get("region")), "A valid region must be supplied"
    assert not isblank(
        connection.get("dataobjects")
    ), "One or more buckets must be supplied"
    return {
        key: val
        for key, val in connection.items()
        if key in _valid_keys and not isblank(connection[key])
    }
