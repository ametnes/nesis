import abc
import datetime
import json
import logging
import os
import tempfile
from typing import Dict, Any, Union

import memcache
import minio
from minio import Minio

import nesis.api.core.util.http as http
from nesis.api.core.document_loaders.stores import SqlDocumentStore
from nesis.api.core.models.entities import Document, Datasource
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
)
from nesis.api.core.util import clean_control, isblank
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


class RagRunner(abc.ABC):
    @abc.abstractmethod
    def run(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: str,
        datasource: Datasource,
        last_modified: datetime.datetime,
        **kwargs,
    ) -> Union[Dict[str, Any], None]:
        pass

    @abc.abstractmethod
    def save(self, **kwargs) -> Document:
        pass

    @abc.abstractmethod
    def delete(self, document: Document, **kwargs) -> None:
        pass


class ExtractRunner(RagRunner):

    def __init__(
        self,
        config: Dict[str, Any],
        destination: Dict[str, Any],
        http_client: http.HttpClient,
    ):
        self._config = config
        self._http_client = http_client
        self._endpoint = self._config

        if destination is None:
            raise ValueError("Destination for the extraction is missing")
        _sql_extraction_store = destination["store"]

        self._extraction_store = SqlDocumentStore(**_sql_extraction_store)
        self._rag_endpoint = (self._config.get("rag") or {}).get("endpoint")

    def run(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: str,
        datasource: Datasource,
        last_modified: datetime.datetime,
        **kwargs,
    ) -> Union[Dict[str, Any], None]:

        if document_id is not None:
            _is_modified = self._is_modified(
                document_id=document_id, last_modified=last_modified
            )
            if _is_modified is None or not _is_modified:
                return

        url = f"{self._rag_endpoint}/v1/extractions/text"

        response = self._http_client.upload(
            url=url,
            filepath=file_path,
            field="file",
            metadata=metadata,
        )
        return json.loads(response)

    def _is_modified(
        self, document_id, last_modified: datetime.datetime
    ) -> Union[bool, None]:
        """
        Here we check if this file has been updated.
        If the file has been updated, we delete it from the vector store and re-ingest the new updated file
        """
        document: Document = self._extraction_store.get(document_id=document_id)

        if document.last_modified < last_modified:
            return False
        try:
            self.delete(document_id=document_id)
        except:
            _LOG.warning(
                f"Failed to delete document {document_id}'s record. Continuing anyway..."
            )
        return True

    def save(self, **kwargs) -> Document:
        return self._extraction_store.save(
            document_id=kwargs["document_id"],
            datasource_id=kwargs["datasource_id"],
            extract_metadata=kwargs["rag_metadata"],
            store_metadata=kwargs["store_metadata"],
            last_modified=kwargs["last_modified"],
            base_uri=kwargs["base_uri"],
            rag_metadata=kwargs["rag_metadata"],
            filename=kwargs["filename"],
        )

    def delete(self, document: Document, **kwargs) -> None:
        self._extraction_store.delete(document_id=document.uuid)


class IngestRunner(RagRunner):

    def __init__(self, config, http_client):
        self._config = config
        self._http_client: http.HttpClient = http_client
        self._endpoint = self._config

        self._rag_endpoint = (self._config.get("rag") or {}).get("endpoint")

    def run(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: str,
        datasource: Datasource,
        last_modified: datetime.datetime,
        **kwargs,
    ) -> Union[Dict[str, Any], None]:

        if document_id is not None:
            _is_modified = self._is_modified(
                document_id=document_id,
                datasource=datasource,
                last_modified=last_modified,
            )
            if _is_modified is None or not _is_modified:
                return

        url = f"{self._rag_endpoint}/v1/ingest/files"

        response = self._http_client.upload(
            url=url,
            filepath=file_path,
            field="file",
            metadata=metadata,
        )
        return json.loads(response)

    def _is_modified(
        self, document_id, datasource: Datasource, last_modified: datetime.datetime
    ) -> Union[bool, None]:
        """
        Here we check if this file has been updated.
        If the file has been updated, we delete it from the vector store and re-ingest the new updated file
        """
        endpoint = datasource.connection["endpoint"]
        document: Document = get_document(document_id=document_id)
        if document is None or document.base_uri != endpoint:
            return False
        elif document.base_uri == endpoint:
            store_metadata = document.store_metadata
            if store_metadata and store_metadata.get("last_modified"):
                if (
                    not strptime(date_string=store_metadata["last_modified"]).replace(
                        tzinfo=None
                    )
                    < last_modified
                ):
                    return False
                try:
                    self.delete(
                        document_id=document_id, rag_metadata=document.rag_metadata
                    )
                except:
                    _LOG.warning(
                        f"Failed to delete document {document_id}'s record. Continuing anyway..."
                    )
                return True
        else:
            return None

    def save(self, **kwargs) -> Document:
        return save_document(
            document_id=kwargs["document_id"],
            filename=kwargs["filename"],
            base_uri=kwargs["base_uri"],
            rag_metadata=kwargs["rag_metadata"],
            store_metadata=kwargs["store_metadata"],
            last_modified=kwargs["last_modified"],
        )

    def delete(self, document: Document, **kwargs) -> None:
        endpoint = (self._config.get("rag") or {}).get("endpoint")
        rag_metadata = kwargs["rag_metadata"]

        # File no longer exists on sharepoint server, so we need to delete from model
        try:
            self._http_client.deletes(
                urls=[
                    f"{endpoint}/v1/ingest/documents/{document_data['doc_id']}"
                    for document_data in rag_metadata.get("data") or []
                ]
            )
            _LOG.info(f"Deleting document {document.filename}")
            delete_document(document_id=document.id)
        except:
            _LOG.warning(
                f"Failed to delete document {document.filename}",
                exc_info=True,
            )


class MinioProcessor(object):
    def __init__(
        self,
        config,
        http_client: http.HttpClient,
        cache_client: memcache.Client,
        datasource: Datasource,
        mode: str = "ingest",
    ):
        self._config = config
        self._http_client = http_client
        self._cache_client = cache_client
        self._datasource = datasource

        match mode:
            case "ingest":
                self._ingest_runner: RagRunner = IngestRunner(
                    config=config, http_client=http_client
                )
            case "extract":
                self._ingest_runner: RagRunner = ExtractRunner(
                    config=config,
                    http_client=http_client,
                    destination=self._datasource.connection.get("destination"),
                )
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
                    _lock_key = clean_control(f"{__name__}/locks/{self_link}")
                    if self._cache_client.add(
                        key=_lock_key, val=_lock_key, time=30 * 60
                    ):
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

        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)

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

            try:
                response_json = self._ingest_runner.run(
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

            self._ingest_runner.save(
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
                        self._ingest_runner.delete(
                            document_id=document.id, rag_metadata=rag_metadata
                        )
                    else:
                        raise

        except:
            _LOG.warn("Error fetching and updating documents", exc_info=True)


def validate_connection_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    _valid_keys = ["endpoint", "user", "password", "dataobjects"]
    assert not isblank(connection.get("endpoint")), "An endpoint must be supplied"
    assert not isblank(
        connection.get("dataobjects")
    ), "One or more buckets must be supplied"
    return {
        key: val
        for key, val in connection.items()
        if key in _valid_keys and not isblank(connection[key])
    }
