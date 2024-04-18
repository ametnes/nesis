import json
import pathlib
import uuid
import memcache
from typing import Dict, Any

import minio

from minio import Minio

import nesis.api.core.util.http as http
import logging
from nesis.api.core.models.entities import Document
from nesis.api.core.services import util
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
    ingest_file,
)
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT
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

        endpoint_parts = endpoint.split("://")
        _minio_client = Minio(
            endpoint=endpoint_parts[1].split("/")[0],
            access_key=access_key,
            secret_key=secret_key,
            secure=endpoint_parts[0] == "https",
        )

        _sync_s3_documents(
            client=_minio_client,
            connection=connection,
            rag_endpoint=rag_endpoint,
            http_client=http_client,
            cache_client=cache_client,
            metadata=metadata,
        )
        _unsync_s3_documents(
            client=_minio_client,
            connection=connection,
            rag_endpoint=rag_endpoint,
            http_client=http_client,
        )
    except:
        _LOG.exception("Error fetching sharepoint documents")


def _sync_s3_documents(
    client: Minio,
    connection: dict,
    rag_endpoint: str,
    http_client: http.HttpClient,
    cache_client: memcache.Client,
    metadata: dict,
) -> None:
    #

    try:

        # We allow setting for unit testing

        # Data objects allow us to specify bucket names
        bucket_names = connection.get("dataobjects")

        bucket_names_parts = bucket_names.split(",")
        work_dir = f"/tmp/{uuid.uuid4()}"
        pathlib.Path(work_dir).mkdir(parents=True)

        _LOG.info(f"Initializing syncing to endpoint {rag_endpoint}")

        for bucket_name in bucket_names_parts:
            try:
                bucket_objects = client.list_objects(bucket_name, recursive=True)
            except:
                _LOG.warn(f"Failed to list objects in bucket {bucket_name}")
                continue
            for item in bucket_objects:
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
                _lock_key = f"{__name__}/locks/{self_link}"
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
                            work_dir=work_dir,
                        )
                    finally:
                        cache_client.delete(_lock_key)
                else:
                    _LOG.info(f"Document {self_link} is already processing")

        _LOG.info(f"Completed syncing to endpoint {rag_endpoint}")

    except:
        _LOG.warning("Error fetching and updating documents", exc_info=True)


def _sync_document(
    client: Minio,
    connection: dict,
    rag_endpoint: str,
    http_client: http.HttpClient,
    metadata: dict,
    bucket_name: str,
    item,
    work_dir: str,
):
    endpoint = connection["endpoint"]
    _metadata = metadata
    file_path = f"{work_dir}/{item.object_name}"
    try:
        _LOG.info(f"Starting syncing object {item.object_name} in bucket {bucket_name}")
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
        if document and document.base_uri == endpoint:
            store_metadata = document.store_metadata
            if store_metadata and store_metadata.get("last_modified"):
                if not strptime(date_string=store_metadata["last_modified"]).replace(
                    tzinfo=None
                ) < item.last_modified.replace(tzinfo=None).replace(microsecond=0):
                    _LOG.debug(
                        f"Skipping document {item.object_name} already up to date"
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
                        _LOG.warn(
                            f"Failed to delete document {document_data['doc_id']}"
                        )

                try:
                    delete_document(document_id=item.etag)
                except:
                    _LOG.warn(
                        f"Failed to delete document {item.object_name}'s record. Continuing anyway..."
                    )

        try:
            response = ingest_file(
                http_client=http_client,
                endpoint=rag_endpoint,
                metadata=_metadata,
                file_path=file_path,
            )
            response_json = json.loads(response)

        except ValueError:
            _LOG.warning(f"File {file_path} ingestion failed", exc_info=True)
            response_json = {}
        except UserWarning:
            _LOG.debug(f"File {file_path} is already processing")
            return

        save_document(
            document_id=item.etag,
            filename=item.object_name,
            base_uri=endpoint,
            rag_metadata=response_json,
            store_metadata={
                "bucket_name": item.bucket_name,
                "object_name": item.object_name,
                "etag": item.etag,
                "size": item.size,
                "last_modified": item.last_modified.strftime(DEFAULT_DATETIME_FORMAT),
                "version_id": item.version_id,
            },
        )

        _LOG.info(f"Done syncing object {item.object_name} in bucket {bucket_name}")
    except Exception as ex:
        _LOG.warn(
            f"Error when getting and ingesting document {item.object_name} - {ex}"
        )


def _unsync_s3_documents(
    client: Minio, connection: dict, rag_endpoint: str, http_client: http.HttpClient
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
                    for document_data in rag_metadata.get("data") or []:
                        try:
                            http_client.delete(
                                url=f"{rag_endpoint}/v1/ingest/documents/{document_data['doc_id']}"
                            )
                        except:
                            _LOG.warn(
                                f"Failed to delete document {document_data['doc_id']}"
                            )
                    _LOG.info(f"Deleting document {document.filename}")
                    delete_document(document_id=document.id)
                else:
                    raise

    except:
        _LOG.warn("Error fetching and updating documents", exc_info=True)
