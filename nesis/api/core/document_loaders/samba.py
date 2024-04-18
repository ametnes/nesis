import uuid
import pathlib
import json
from datetime import datetime
from typing import Dict, Any

import smbprotocol
from smbclient import scandir, stat, shutil

import logging
from nesis.api.core.models.entities import Document
from nesis.api.core.services import util
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
    ValidationException,
    ingest_file,
)
from nesis.api.core.util import http
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT, DEFAULT_SAMBA_PORT
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


def fetch_documents(
    connection: Dict[str, str],
    rag_endpoint: str,
    http_client: http.HttpClient,
    metadata: Dict[str, Any],
) -> None:
    try:
        _sync_samba_documents(connection, rag_endpoint, http_client, metadata)
    except:
        _LOG.exception(f"Error syncing documents")

    try:
        _unsync_samba_documents(connection, rag_endpoint, http_client)
    except Exception as ex:
        _LOG.exception(f"Error unsyncing documents")


def validate_connection_info(connection):
    port = connection.get("port")
    if port is None or not port:
        connection["port"] = DEFAULT_SAMBA_PORT
    elif not port.isnumeric():
        raise ValidationException("Port value cannot be non numeric")

    if connection.get("endpoint") is None or not connection.get("endpoint"):
        raise ValidationException("Endpoint value cannot be null or empty")

    if connection.get("user") is None or not connection.get("user"):
        raise ValidationException("Username value cannot be null or empty")

    if connection.get("password") is None or not connection.get("password"):
        raise ValidationException("Password value cannot be null or empty")

    try:
        _connect_samba_server(connection)
    except ValidationException as sb:
        _LOG.exception(
            f"Failed to connect to samba server at {connection['endpoint']}",
            stack_info=True,
        )
        raise
    return connection


def _connect_samba_server(connection):
    username = connection["user"]
    password = connection["password"]
    endpoint = connection["endpoint"]
    port = connection["port"]
    try:
        scandir(endpoint, username=username, password=password, port=port)
    except Exception as ex:
        _LOG.exception(f"Error while connecting to samba server {endpoint} - {ex}")
        raise


def _sync_samba_documents(connection, rag_endpoint, http_client, metadata):

    username = connection["user"]
    password = connection["password"]
    endpoint = connection["endpoint"]
    port = connection["port"]
    # These are any folder specified to scope the sync to
    dataobjects = connection.get("dataobjects") or ""

    dataobjects_parts = [do.strip() for do in dataobjects.split(",")]

    try:
        file_shares = scandir(endpoint, username=username, password=password, port=port)
    except Exception as ex:
        _LOG.exception(f"Error while scanning share on samba server {endpoint} - {ex}")
        raise

    work_dir = f"/tmp/{uuid.uuid4()}"
    pathlib.Path(work_dir).mkdir(parents=True)

    for file_share in file_shares:
        if (
            len(dataobjects_parts) > 0
            and file_share.is_dir()
            and file_share.name not in dataobjects_parts
        ):
            continue
        try:
            _process_file(
                connection, file_share, work_dir, http_client, rag_endpoint, metadata
            )
        except:
            _LOG.warn(
                f"Error fetching and updating documents from shared_file share {file_share.path} - ",
                exc_info=True,
            )
    _LOG.info(
        f"Completed syncing files from samba server {endpoint} "
        f"to endpoint {rag_endpoint}"
    )


def _process_file(
    connection, file_share, work_dir, http_client, rag_endpoint, metadata
):
    username = connection["user"]
    password = connection["password"]
    endpoint = connection["endpoint"]
    port = connection["port"]

    if file_share.is_dir():
        if not file_share.name.startswith("."):
            dir_files = scandir(
                file_share.path, username=username, password=password, port=port
            )
            for dir_file in dir_files:
                _process_file(
                    connection, dir_file, work_dir, http_client, rag_endpoint, metadata
                )
        return

    file_name = file_share.name
    file_stats = stat(file_share.path, username=username, password=password, port=port)
    last_change_datetime = datetime.fromtimestamp(file_stats.st_chgtime)

    try:
        file_path = f"{work_dir}/{file_share.name}"
        file_unique_id = f"{uuid.uuid5(uuid.NAMESPACE_DNS, file_share.path)}"

        _metadata = {
            **(metadata or {}),
            "file_name": file_share.path,
            "self_link": file_share.path,
        }

        _LOG.info(
            f"Starting syncing shared_file {file_name} in shared directory share {file_share.path}"
        )

        try:
            shutil.copyfile(
                file_share.path,
                file_path,
                username=username,
                password=password,
                port=port,
            )
        except Exception as ex:
            _LOG.warn(
                f"Failed to copy contents of shared_file {file_name} from shared location {file_share.path}",
                exc_info=True,
            )
            return

        """
        Here we check if this file has been updated.
        If the file has been updated, we delete it from the vector store and re-ingest the new updated file
        """
        document: Document = get_document(document_id=file_unique_id)
        if document and document.base_uri == endpoint:
            store_metadata = document.store_metadata
            if store_metadata and store_metadata.get("last_modified"):
                if not strptime(date_string=store_metadata["last_modified"]).replace(
                    tzinfo=None
                ) < last_change_datetime.replace(tzinfo=None).replace(microsecond=0):
                    _LOG.debug(f"Skipping shared_file {file_name} already up to date")
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
                            f"Failed to delete document {document_data['doc_id']}",
                            exc_info=True,
                        )
                try:
                    delete_document(document_id=file_unique_id)
                except:
                    _LOG.warn(
                        f"Failed to delete shared_file {file_name}'s record. Continuing anyway...",
                        exc_info=True,
                    )

        file_metadata = {
            "shared_folder": file_share.name,
            "file_path": file_share.path,
            "file_id": file_unique_id,
            "size": file_stats.st_size,
            "name": file_name,
            "last_modified": last_change_datetime.strftime(DEFAULT_DATETIME_FORMAT),
        }

        try:
            response = ingest_file(
                http_client=http_client,
                endpoint=rag_endpoint,
                metadata=_metadata,
                file_path=file_path,
            )
        except UserWarning:
            _LOG.debug(f"File {file_path} is already processing")
            return
        response_json = json.loads(response)

        save_document(
            document_id=file_unique_id,
            filename=file_name,
            base_uri=endpoint,
            rag_metadata=response_json,
            store_metadata=file_metadata,
        )

        _LOG.info(f"Done syncing shared_file {file_name} in location {file_share.path}")
    except Exception as ex:
        _LOG.warn(
            f"Error when getting and ingesting shared_file {file_name} - {ex}",
            exc_info=True,
        )
    _LOG.info(
        f"Completed syncing files from shared_file share {file_share.path} to endpoint {rag_endpoint}"
    )


def _unsync_samba_documents(connection, rag_endpoint, http_client):
    try:
        username = connection["user"]
        password = connection["password"]
        endpoint = connection["endpoint"]
        port = connection["port"]

        work_dir = f"/tmp/{uuid.uuid4()}"
        pathlib.Path(work_dir).mkdir(parents=True)

        documents = get_documents(base_uri=endpoint)
        for document in documents:
            store_metadata = document.store_metadata
            rag_metadata = document.rag_metadata

            file_path = store_metadata["file_path"]
            try:
                stat(file_path, username=username, password=password, port=port)
            except smbprotocol.exceptions.SMBOSError as error:
                if "No such file" not in str(error):
                    raise
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
                _LOG.info(f"Deleting document {document.filename}")
                delete_document(document_id=document.id)
        _LOG.info(f"Completed unsyncing files from endpoint {rag_endpoint}")
    except:
        _LOG.warn("Error fetching and updating documents", exc_info=True)
