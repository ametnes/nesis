import json
import logging
import pathlib
import tempfile
from typing import Dict, Any

import boto3
import memcache

import nesis.api.core.util.http as http
from nesis.api.core.models.entities import Document
from nesis.api.core.services import util
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
    ingest_file,
)
from nesis.api.core.util import clean_control
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


def fetch_documents(
    connection: Dict[str, str],
    rag_endpoint: str,
    http_client: http.HttpClient,
    cache_client: memcache.Client,
    metadata: Dict[str, Any],
) -> None:
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

        _sync_documents(
            client=s3_client,
            connection=connection,
            rag_endpoint=rag_endpoint,
            http_client=http_client,
            cache_client=cache_client,
            metadata=metadata,
        )
        _unsync_documents(
            client=s3_client,
            connection=connection,
            rag_endpoint=rag_endpoint,
            http_client=http_client,
        )
    except Exception as ex:
        _LOG.exception(f"Error fetching s3 documents - {ex}")


def _sync_documents(
    client,
    connection: dict,
    rag_endpoint: str,
    http_client: http.HttpClient,
    cache_client: memcache.Client,
    metadata: dict,
) -> None:

    try:

        # Data objects allow us to specify bucket names
        bucket_paths = connection.get("dataobjects")
        if bucket_paths is None:
            _LOG.warning("No bucket names supplied, so I can't do much")

        bucket_paths_parts = bucket_paths.split(",")

        _LOG.info(f"Initializing syncing to endpoint {rag_endpoint}")

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
                    if cache_client.add(key=_lock_key, val=_lock_key, time=30 * 60):
                        try:
                            _sync_document(
                                client=client,
                                connection=connection,
                                rag_endpoint=rag_endpoint,
                                http_client=http_client,
                                metadata=_metadata,
                                bucket_name=bucket_name,
                                item=item,
                            )
                        finally:
                            cache_client.delete(_lock_key)
                    else:
                        _LOG.info(f"Document {self_link} is already processing")

        _LOG.info(f"Completed syncing to endpoint {rag_endpoint}")

    except:
        _LOG.warning("Error fetching and updating documents", exc_info=True)


def _sync_document(
    client,
    connection: dict,
    rag_endpoint: str,
    http_client: http.HttpClient,
    metadata: dict,
    bucket_name: str,
    item,
):
    endpoint = connection["endpoint"]
    _metadata = metadata

    with tempfile.NamedTemporaryFile(
        dir=tempfile.gettempdir(),
    ) as tmp:
        key_parts = item["Key"].split("/")

        path_to_tmp = f"{str(pathlib.Path(tmp.name).absolute())}-{key_parts[-1]}"

        try:
            _LOG.info(f"Starting syncing object {item['Key']} in bucket {bucket_name}")
            # Write item to file
            client.download_file(bucket_name, item["Key"], path_to_tmp)

            document: Document = get_document(document_id=item["ETag"])
            if document and document.base_uri == endpoint:
                store_metadata = document.store_metadata
                if store_metadata and store_metadata.get("last_modified"):
                    last_modified = store_metadata["last_modified"]
                    if not strptime(date_string=last_modified).replace(
                        tzinfo=None
                    ) < item["LastModified"].replace(tzinfo=None).replace(
                        microsecond=0
                    ):
                        _LOG.debug(
                            f"Skipping document {item['Key']} already up to date"
                        )
                        return
                    rag_metadata: dict = document.rag_metadata
                    if rag_metadata is None:
                        return
                    for document_data in rag_metadata.get("data") or []:
                        try:
                            util.un_ingest_file(
                                http_client=http_client,
                                endpoint=rag_endpoint,
                                doc_id=document_data["doc_id"],
                            )
                        except:
                            _LOG.warning(
                                f"Failed to delete document {document_data['doc_id']}"
                            )

                    try:
                        delete_document(document_id=document.id)
                    except:
                        _LOG.warning(
                            f"Failed to delete document {item.object_name}'s record. Continuing anyway..."
                        )

            try:
                response = ingest_file(
                    http_client=http_client,
                    endpoint=rag_endpoint,
                    metadata=_metadata,
                    file_path=path_to_tmp,
                )
                response_json = json.loads(response)

            except ValueError:
                _LOG.warning(f"File {path_to_tmp} ingestion failed", exc_info=True)
                response_json = {}
            except UserWarning:
                _LOG.debug(f"File {path_to_tmp} is already processing")
                return

            save_document(
                document_id=item["ETag"],
                filename=item["Key"],
                base_uri=endpoint,
                rag_metadata=response_json,
                store_metadata={
                    "bucket_name": bucket_name,
                    "object_name": item["Key"],
                    "etag": item["ETag"],
                    "size": item["Size"],
                    "last_modified": str(item["LastModified"]),
                },
            )

            _LOG.info(f"Done syncing object {item['Key']} in bucket {bucket_name}")
        except Exception as ex:
            _LOG.warning(
                f"Error when getting and ingesting document {item['Key']} - {ex}"
            )


def _unsync_documents(
    client, connection: dict, rag_endpoint: str, http_client: http.HttpClient
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
                client.head_object(Bucket=bucket_name, Key=object_name)
            except Exception as ex:
                str_ex = str(ex)
                if not ("ClientError" in str_ex and "not found" in str_ex.lower()):
                    raise
                for document_data in rag_metadata.get("data") or []:
                    try:
                        http_client.delete(
                            url=f"{rag_endpoint}/v1/ingest/documents/{document_data['doc_id']}"
                        )
                    except:
                        _LOG.warning(
                            f"Failed to delete document {document_data['doc_id']}"
                        )
                _LOG.info(f"Deleting document {document.filename}")
                delete_document(document_id=document.id)

    except:
        _LOG.warn("Error fetching and updating documents", exc_info=True)
