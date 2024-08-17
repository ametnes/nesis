import json
import pathlib
import uuid
import tempfile
from typing import Dict, Any
from urllib.parse import urlparse

import memcache

from office365.sharepoint.client_context import ClientContext
from office365.runtime.client_request_exception import ClientRequestException

from nesis.api.core.document_loaders.loader_helper import DocumentProcessor
from nesis.api.core.util import http, clean_control, isblank
import logging
from nesis.api.core.models.entities import Document, Datasource
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
        self._futures = []

    def run(self, metadata: Dict[str, Any]):

        try:

            connection = self._datasource.connection
            site_url = connection.get("endpoint")
            client_id = connection.get("client_id")
            tenant = connection.get("tenant_id")
            thumbprint = connection.get("thumbprint")

            with tempfile.NamedTemporaryFile(dir=tempfile.gettempdir()) as tmp:
                cert_path = (
                    f"{str(pathlib.Path(tmp.name).absolute())}-{uuid.uuid4()}.key"
                )
                pathlib.Path(cert_path).write_text(connection["certificate"])

                _sharepoint_context = ClientContext(site_url).with_client_certificate(
                    tenant=tenant,
                    client_id=client_id,
                    thumbprint=thumbprint,
                    cert_path=cert_path,
                )

                self._sync_sharepoint_documents(
                    sp_context=_sharepoint_context,
                    metadata=metadata,
                )
                self._unsync_sharepoint_documents(
                    sp_context=_sharepoint_context,
                )
        except Exception as ex:
            _LOG.exception(f"Error fetching sharepoint documents - {ex}")

    def _sync_sharepoint_documents(self, sp_context, metadata):
        try:

            if sp_context is None:
                raise Exception(
                    "Sharepoint context is null, cannot proceed with document processing."
                )

            # Data objects allow us to specify folder names
            connection = self._datasource.connection
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

                self._process_folder_files(
                    sharepoint_folder,
                    metadata=metadata,
                )

                # Recursively get all the child folders
                _child_folders_recursive = sharepoint_folder.get_folders(
                    True
                ).execute_query()
                for _child_folder in _child_folders_recursive:
                    self._process_folder_files(
                        _child_folder,
                        metadata=metadata,
                    )

        except Exception as file_ex:
            _LOG.exception(
                f"Error fetching and updating documents - Error: {file_ex}",
                exc_info=True,
            )

    def _process_file(
        self,
        file,
        metadata,
    ):
        connection = self._datasource.connection
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
        if self._cache_client.add(key=_lock_key, val=_lock_key, time=30 * 60):
            try:
                self._sync_document(
                    metadata=_metadata,
                    file=file,
                )
            finally:
                self._cache_client.delete(_lock_key)
        else:
            _LOG.info(f"Document {self_link} is already processing")

    def _process_folder_files(self, folder, metadata):
        # process files in folder
        _files = folder.get_files(False).execute_query()
        for file in _files:
            self._process_file(
                file=file,
                metadata=metadata,
            )

    def _sync_document(
        self,
        metadata: dict,
        file,
    ):
        connection = self._datasource.connection
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

                # How can we refine this for efficiency
                with open(path_to_tmp, "wb") as local_file:
                    file.download(local_file).execute_query()

                self.sync(
                    site_url,
                    path_to_tmp,
                    last_modified=file.time_last_modified,
                    metadata=metadata,
                    store_metadata={
                        "filename": file.name,
                        "file_url": file.serverRelativeUrl,
                        "etag": file.unique_id,
                        "size": file.length,
                        "author": file.author,
                        "last_modified": file.time_last_modified.strftime(
                            DEFAULT_DATETIME_FORMAT
                        ),
                    },
                )
            except:
                _LOG.warning(
                    f"Error when getting and ingesting file {file.name}", exc_info=True
                )

    def _unsync_sharepoint_documents(self, sp_context):

        def clean(**kwargs):
            store_metadata = kwargs["store_metadata"]

            file_url = store_metadata["file_url"]
            try:
                # Check that the file still exists on the sharepoint server
                sp_context.web.get_file_by_server_relative_url(
                    file_url
                ).get().execute_query()
            except ClientRequestException as e:
                if e.response.status_code == 404:
                    return True
                else:
                    raise

        try:
            self.unsync(clean=clean)
        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)


def validate_connection_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    _valid_keys = [
        "endpoint",
        "tenant_id",
        "client_id",
        "thumbprint",
        "certificate",
        "dataobjects",
    ]
    assert not isblank(connection.get("endpoint")), "A site url must be supplied"
    assert not isblank(connection.get("client_id")), "A client_id must be supplied"
    assert not isblank(connection.get("tenant_id")), "A client_id must be supplied"
    assert not isblank(connection.get("thumbprint")), "A thumbprint must be supplied"
    assert not isblank(
        connection.get("certificate")
    ), "A valid certificate must be supplied"
    return {
        key: val
        for key, val in connection.items()
        if key in _valid_keys and not isblank(connection[key])
    }
