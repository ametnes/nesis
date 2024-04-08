import json
import os
import pathlib
import uuid

from office365.sharepoint.client_context import ClientContext
from office365.runtime.client_request_exception import ClientRequestException

import nesis.api.core.util.http as http
import logging
from nesis.api.core.models.entities import Document
from nesis.api.core.services.util import (
    save_document,
    get_document,
    delete_document,
    get_documents,
)
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT
from nesis.api.core.util.dateutil import strptime

_LOG = logging.getLogger(__name__)

_sharepoint_context = None


def fetch_documents(**kwargs) -> None:
    try:
        rag_endpoint = kwargs["rag_endpoint"]
        connection = kwargs["connection"]

        _sync_sharepoint_documents(
            **kwargs, connection=connection, rag_endpoint=rag_endpoint
        )
        _unsync_sharepoint_documents(
            **kwargs, connection=connection, rag_endpoint=rag_endpoint
        )
    except:
        _LOG.exception("Error fetching sharepoint documents")


def _sync_sharepoint_documents(**kwargs):
    global _sharepoint_context
    config = kwargs["config"]["tasks"]["fetch_documents"].get("config") or {}
    http_client: http.HttpClient = kwargs["http_client"]
    doc_store_connection = kwargs["connection"]
    try:
        site_url = doc_store_connection.get("site_url")
        client_id = doc_store_connection.get("client_id")
        client_secret = doc_store_connection.get("secret_key")

        if _sharepoint_context is None:
            _sharepoint_context = ClientContext(site_url).with_client_credentials(
                client_id=client_id, client_secret=client_secret
            )

        file_locations = doc_store_connection.get("file_locations")

        rag_endpoint = kwargs["rag_endpoint"]

        location_names = file_locations.split(",")
        work_dir = f"/tmp/{uuid.uuid4()}"
        pathlib.Path(work_dir).mkdir(parents=True)

        _LOG.info(f"Initializing sharepoint syncing to endpoint {rag_endpoint}")

        # Sharepoint stores documents in different ways, in folders and there is a concept of lists Most document
        # libraries are stores as lists, thus we can safely assume that the locations provided in the settings are
        # Sharepoint document libraries (lists) We use this assumption to access the respective files

        for location_name in location_names:
            try:
                folder = _sharepoint_context.web.lists.get_by_title(
                    location_name
                ).root_folder
                files = folder.get_files(recursive=True).execute_query()
            except:
                _LOG.warn(f"Failed to list files in file location {location_name}")
                continue
            for file in files:
                file_path = f"{work_dir}/{location_name}"
                try:
                    _LOG.info(
                        f"Starting syncing file {file.name} in location {location_name}"
                    )
                    downloaded_file_name = os.path.join(file_path, file.name)
                    # How can we refine this for efficiency
                    with open(downloaded_file_name, "wb") as local_file:
                        file.download(local_file).execute_query()

                    document: Document = get_document(document_id=file.unique_id)
                    if document:
                        store_metadata = document.store_metadata
                        if store_metadata and store_metadata.get("last_modified"):
                            if not strptime(
                                date_string=store_metadata["last_modified"]
                            ).replace(tzinfo=None) < file.last_modified.replace(
                                tzinfo=None
                            ).replace(
                                microsecond=0
                            ):
                                _LOG.debug(
                                    f"Skipping file {file.name} already up to date"
                                )
                                continue
                            rag_metadata: dict = document.rag_metadata
                            if rag_metadata is None:
                                continue
                            for document_data in rag_metadata.get("data") or []:
                                try:
                                    http_client.delete(
                                        url=f"{rag_endpoint}/v1/ingest/{document_data['doc_id']}"
                                    )
                                except:
                                    _LOG.warn(
                                        f"Failed to delete document {document_data['doc_id']}"
                                    )

                            try:
                                delete_document(document_id=file.unique_id)
                            except:
                                _LOG.warn(
                                    f"Failed to delete file {file.name}'s record. Continuing anyway..."
                                )

                    response = http_client.upload(
                        url=f"{rag_endpoint}/v1/ingest",
                        filepath=downloaded_file_name,
                        field="file",
                    )
                    response_json = json.loads(response)

                    save_document(
                        document_id=file.unique_id,
                        filename=file.name,
                        base_uri=site_url,
                        rag_metadata=response_json,
                        store_metadata={
                            "file_url": f"{location_name}/{file.name}",
                            "file_name": file.name,
                            "etag": file.unique_id,
                            "size": file.length,
                            "author": file.author,
                            "last_modified": file.time_last_modified.strftime(
                                DEFAULT_DATETIME_FORMAT
                            ),
                            "version_id": f"{file.major_version}-{file.minor_version}",
                        },
                    )

                    _LOG.info(
                        f"Done syncing file {file.name} in location {location_name}"
                    )
                except Exception as ex:
                    _LOG.warn(
                        f"Error when getting and ingesting file {file.name} - {ex}"
                    )

        _LOG.info(f"Completed syncing to endpoint {rag_endpoint}")

    except:
        _LOG.warn("Error fetching and updating documents", exc_info=True)


def _unsync_sharepoint_documents(**kwargs):
    global _sharepoint_context
    http_client: http.HttpClient = kwargs["http_client"]
    doc_store_connection = kwargs["connection"]
    rag_endpoint = kwargs["rag_endpoint"]

    try:
        site_url = doc_store_connection.get("site_url")
        client_id = doc_store_connection.get("client_id")
        client_secret = doc_store_connection.get("secret_key")

        if _sharepoint_context is None:
            _sharepoint_context = ClientContext(site_url).with_client_credentials(
                client_id=client_id, client_secret=client_secret
            )

        documents = get_documents(base_uri=site_url)
        for document in documents:
            store_metadata = document.store_metadata
            rag_metadata = document.rag_metadata
            file_url = store_metadata["file_url"]
            try:
                # Check that the file still exists on the sharepoint server
                _sharepoint_context.web.get_file_by_server_relative_url(
                    file_url
                ).get().execute_query()
            except ClientRequestException as e:
                if e.response.status_code == 404:
                    # File no longer exists on sharepoint server so we need to delete from model
                    for document_data in rag_metadata.get("data") or []:
                        try:
                            http_client.delete(
                                url=f"{rag_endpoint}/v1/ingest/{document_data['doc_id']}"
                            )
                        except:
                            _LOG.warn(
                                f"Failed to delete document {document_data['doc_id']}"
                            )
                    _LOG.info(f"Deleting document {document.filename}")
                    delete_document(document_id=document.id)

    except:
        _LOG.warn("Error fetching and updating documents", exc_info=True)
