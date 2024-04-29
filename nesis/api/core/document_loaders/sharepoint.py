import json
import pathlib
import uuid
import tempfile
from typing import Dict, Any
from urllib.parse import urlparse

import memcache

from office365.sharepoint.client_context import ClientContext
from office365.runtime.client_request_exception import ClientRequestException

from nesis.api.core.util import http, clean_control, isblank
import logging
from nesis.api.core.models.entities import Document
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
    un_ingest_file,
    ingest_file,
)
from nesis.api.core.util import isblank
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)


def fetch_documents(
    connection: Dict[str, str],
    rag_endpoint: str,
    http_client: http.HttpClient,
    metadata: Dict[str, Any],
    cache_client: memcache.Client,
) -> None:
    try:

        site_url = connection.get("endpoint")
        client_id = connection.get("client_id")
        tenant = connection.get("tenant_id")
        thumbprint = connection.get("thumbprint")

        with tempfile.NamedTemporaryFile(dir=tempfile.gettempdir()) as tmp:
            cert_path = f"{str(pathlib.Path(tmp.name).absolute())}-{uuid.uuid4()}.key"
            pathlib.Path(cert_path).write_text(connection["certificate"])

            _sharepoint_context = ClientContext(site_url).with_client_certificate(
                tenant=tenant,
                client_id=client_id,
                thumbprint=thumbprint,
                cert_path=cert_path,
            )

            _sync_sharepoint_documents(
                sp_context=_sharepoint_context,
                connection=connection,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
                metadata=metadata,
                cache_client=cache_client,
            )
            _unsync_sharepoint_documents(
                sp_context=_sharepoint_context,
                connection=connection,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
            )
    except Exception as ex:
        _LOG.exception(f"Error fetching sharepoint documents - {ex}")


def _get_temp_certificate_path(connection) -> str:
    cert_path = ""
    certificate_details = connection["certificate"]
    try:
        with tempfile.NamedTemporaryFile(
            dir=tempfile.gettempdir(), delete_on_close=False
        ) as tmp:
            cert_path = f"{str(pathlib.Path(tmp.name).absolute())}-{uuid.uuid4()}.key"

            with open(cert_path, "w") as svc_file:
                svc_file.write(certificate_details)
    except Exception as ex:
        _LOG.error(f"Failed to generate certificate path - {ex}")
    return cert_path


def _sync_sharepoint_documents(
    sp_context, connection, rag_endpoint, http_client, metadata, cache_client
):
    try:
        _LOG.info(f"Initializing sharepoint syncing to endpoint {rag_endpoint}")

        if sp_context is None:
            raise Exception(
                "Sharepoint context is null, cannot proceed with document processing."
            )

        # Data objects allow us to specify folder names
        sharepoint_folders = connection.get("dataobjects")
        if sharepoint_folders is None:
            _LOG.warning("Sharepoint folders are specified, so I can't do much")

        sp_folders = sharepoint_folders.split(",")

        root_folder = sp_context.web.default_document_library().root_folder

        for folder_name in sp_folders:
            sharepoint_folder = root_folder.folders.get_by_path(folder_name)

            if sharepoint_folder is None:
                _LOG.warning(
                    f"Cannot retrieve Sharepoint folder {sharepoint_folder} proceeding to process other folders"
                )
                continue

            _process_folder_files(
                sharepoint_folder,
                connection=connection,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
                metadata=metadata,
                cache_client=cache_client,
            )

            # Recursively get all the child folders
            _child_folders_recursive = sharepoint_folder.get_folders(
                True
            ).execute_query()
            for _child_folder in _child_folders_recursive:
                _process_folder_files(
                    _child_folder,
                    connection=connection,
                    rag_endpoint=rag_endpoint,
                    http_client=http_client,
                    metadata=metadata,
                    cache_client=cache_client,
                )
        _LOG.info(f"Completed syncing to endpoint {rag_endpoint}")

    except Exception as file_ex:
        _LOG.exception(
            f"Error fetching and updating documents - Error: {file_ex}", exc_info=True
        )


def _process_file(file, connection, rag_endpoint, http_client, metadata, cache_client):
    site_url = connection.get("endpoint")
    parsed_site_url = urlparse(site_url)
    site_root_url = "{uri.scheme}://{uri.netloc}".format(uri=parsed_site_url)
    self_link = f"{site_root_url}{file.serverRelativeUrl}"
    _metadata = {
        **(metadata or {}),
        "file_name": file.name,
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
                connection=connection,
                rag_endpoint=rag_endpoint,
                http_client=http_client,
                metadata=_metadata,
                file=file,
            )
        finally:
            cache_client.delete(_lock_key)
    else:
        _LOG.info(f"Document {self_link} is already processing")


def _process_folder_files(
    folder, connection, rag_endpoint, http_client, metadata, cache_client
):
    # process files in folder
    _files = folder.get_files(False).execute_query()
    for file in _files:
        _process_file(
            file=file,
            connection=connection,
            rag_endpoint=rag_endpoint,
            http_client=http_client,
            metadata=metadata,
            cache_client=cache_client,
        )


def _sync_document(
    connection: dict,
    rag_endpoint: str,
    http_client: http.HttpClient,
    metadata: dict,
    file,
):
    site_url = connection["endpoint"]
    _metadata = metadata

    with tempfile.NamedTemporaryFile(
        dir=tempfile.gettempdir(),
    ) as tmp:
        key_parts = file.serverRelativeUrl.split("/")

        path_to_tmp = f"{str(pathlib.Path(tmp.name).absolute())}-{key_parts[-1]}"

        try:
            _LOG.info(
                f"Starting syncing file {file.name} from {file.serverRelativeUrl}"
            )
            # Write item to file
            downloaded_file_name = path_to_tmp  # os.path.join(path_to_tmp, file.name)
            # How can we refine this for efficiency
            with open(downloaded_file_name, "wb") as local_file:
                file.download(local_file).execute_query()

            document: Document = get_document(document_id=file.unique_id)
            if document and document.base_uri == site_url:
                store_metadata = document.store_metadata
                if store_metadata and store_metadata.get("last_modified"):
                    last_modified = store_metadata["last_modified"]
                    if (
                        not strptime(date_string=last_modified).replace(tzinfo=None)
                        < file.time_last_modified
                    ):
                        _LOG.debug(
                            f"Skipping sharepoint document {file.name} already up to date"
                        )
                        return
                    rag_metadata: dict = document.rag_metadata
                    if rag_metadata is None:
                        return
                    for document_data in rag_metadata.get("data") or []:
                        try:
                            un_ingest_file(
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
                            f"Failed to delete document {file.name}'s record. Continuing anyway..."
                        )
            try:
                response = ingest_file(
                    http_client=http_client,
                    endpoint=rag_endpoint,
                    metadata=_metadata,
                    file_path=downloaded_file_name,
                )
                response_json = json.loads(response)

            except ValueError:
                _LOG.warning(
                    f"File {downloaded_file_name} ingestion failed", exc_info=True
                )
                response_json = {}
            except UserWarning:
                _LOG.debug(f"File {downloaded_file_name} is already processing")
                return

            save_document(
                document_id=file.unique_id,
                filename=file.name,
                base_uri=site_url,
                rag_metadata=response_json,
                store_metadata={
                    "file_name": file.name,
                    "file_url": file.serverRelativeUrl,
                    "etag": file.unique_id,
                    "size": file.length,
                    "author": file.author,
                    "last_modified": file.time_last_modified.strftime(
                        DEFAULT_DATETIME_FORMAT
                    ),
                },
            )
            _LOG.info(f"Done syncing object {file.name} in at {file.serverRelativeUrl}")
        except Exception as ex:
            _LOG.warning(f"Error when getting and ingesting file {file.name} - {ex}")


def _unsync_sharepoint_documents(sp_context, http_client, rag_endpoint, connection):

    try:
        site_url = connection.get("endpoint")

        if sp_context is None:
            raise Exception(
                "Sharepoint context is null, cannot proceed with document processing."
            )

        documents = get_documents(base_uri=site_url)
        for document in documents:
            store_metadata = document.store_metadata
            rag_metadata = document.rag_metadata
            file_url = store_metadata["file_url"]
            try:
                # Check that the file still exists on the sharepoint server
                sp_context.web.get_file_by_server_relative_url(
                    file_url
                ).get().execute_query()
            except ClientRequestException as e:
                if e.response.status_code == 404:
                    # File no longer exists on sharepoint server so we need to delete from model
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
            except Exception as ex:
                _LOG.warning(
                    f"Failed to retrieve file {file_url} from sharepoint - {ex}"
                )
    except:
        _LOG.warning("Error fetching and updating documents", exc_info=True)


def validate_connection_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    _valid_keys = [
        "endpoint",
        "tenant",
        "client_id",
        "thumbprint",
        "certificate",
        "dataobjects",
    ]
    assert not isblank(connection.get("endpoint")), "A site url must be supplied"
    assert not isblank(connection.get("client_id")), "A client_id must be supplied"
    assert not isblank(connection.get("thumbprint")), "A thumbprint must be supplied"
    assert not isblank(
        connection.get("certificate")
    ), "A valid certificate must be supplied"
    return {
        key: val
        for key, val in connection.items()
        if key in _valid_keys and not isblank(connection[key])
    }
