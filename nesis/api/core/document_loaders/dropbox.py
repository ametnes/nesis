import datetime

from langchain_community.document_loaders import DropboxLoader
import logging
import uuid
from dropbox import DropboxOAuth2FlowNoRedirect

from nesis.api.core.document_loaders.loader_helper import upload_document_to_llm
from nesis.api.core.services.util import save_document
from nesis.api.core.services.settings import SettingsService

_LOG = logging.getLogger(__name__)


def fetch_documents(settings, rag_endpoint, http_client) -> None:
    try:
        settings = _get_dropbox_oauth_refresh_token(settings)
        _sync_dropbox_documents(settings, rag_endpoint, http_client)
        _unsync_dropbox_documents(settings, rag_endpoint, http_client)
    except Exception as ex:
        _LOG.exception(f"Error fetching sharepoint documents - {ex}")
        raise


def _get_dropbox_oauth_refresh_token(settings):
    refresh_token = settings["connection"].get("refresh_token")

    if refresh_token is not None:
        return refresh_token
    else:
        # we first check if the refresh token exists
        app_key = settings["connection"]["app_key"]

        auth_flow = DropboxOAuth2FlowNoRedirect(
            app_key, use_pkce=True, token_access_type="offline"
        )

        authorize_url = auth_flow.start()
        print("1. Go to: " + authorize_url)
        print('2. Click "Allow" (you might have to log in first).')
        print("3. Copy the authorization code.")
        auth_code = (
            "yAvACKlMHT8AAAAAAAAAF8nXH7-PH2eMzve2RXbSok4".strip()
        )  # we need to find a way of getting this code

        try:
            oauth_result = auth_flow.finish(auth_code)

            # we need to save this refresh token to the settings
            settings["connection"]["refresh_token"] = oauth_result.refresh_token
            settings = SettingsService.create_or_update(setting=settings)
        except Exception as e:
            _LOG(f"Failed to login to Dropbox with error - {e}")
            raise
    return settings


def _sync_dropbox_documents(settings, rag_endpoint, http_client):
    dropbox_access_token = settings["access_token"]
    dropbox_folders = settings["dropbox_folders"]

    folder_names = dropbox_folders.split(",")

    _LOG.info(f"Initializing dropbox syncing to endpoint {rag_endpoint}")

    for folder in folder_names:
        try:
            loader = DropboxLoader(
                dropbox_access_token=dropbox_access_token,
                dropbox_folder_path=f"/{folder}",
                recursive=True,
            )
            documents = loader.load()
        except:
            _LOG.exception(f"Failed to load dropbox files from {folder}")
            continue
        for document in documents:
            try:
                # get generate a file unique Id from the source metadata_value.
                # This is supposed to be the same if source does not change
                file_source = document.metadata["source"]
                file_unique_id = f"{uuid.uuid5(uuid.NAMESPACE_DNS, file_source)}"

                file_metadata = {
                    "name": document.metadata["title"],
                    "folder_name": folder,
                    "file_source": file_source,
                    "unique_id": file_unique_id,
                    "last_modified": datetime.datetime.now(datetime.UTC).strftime(
                        "%Y%m%dT%H%M%SZ"
                    ),
                }

                upload_response = upload_document_to_llm(
                    upload_document=document,
                    file_metadata=file_metadata,
                    http_client=http_client,
                    rag_endpoint=rag_endpoint,
                )

                # If the document has been successfully uploaded to LLM we save details in document database
                if upload_response is not None:
                    save_document(
                        document_id=file_unique_id,
                        filename=file_metadata["title"],
                        base_uri=file_source,
                        rag_metadata=upload_response,
                        store_metadata=file_metadata,
                    )

                _LOG.info(
                    f"Done syncing file {file_metadata['name']} in location {folder}"
                )
            except Exception as ex:
                _LOG.warn(
                    f"Error when getting and ingesting file {document['metadata']['title']} - {ex}"
                )

    _LOG.info(f"Completed syncing to endpoint {rag_endpoint}")


def _unsync_dropbox_documents(settings, rag_endpoint, http_client):
    settings = settings
    # TODO implement unsync of documents from dropbox
