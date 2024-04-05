import datetime

import logging
import uuid
import os
import pathlib
import json

from nesis.api.core.document_loaders.loader_helper import upload_document_to_llm
from nesis.api.core.services.util import save_document


_LOG = logging.getLogger(__name__)


def fetch_documents(connection, llm_endpoint, http_client) -> None:
    try:
        _sync_google_documents(connection, llm_endpoint, http_client)
        # _unsync_google_documents(settings, llm_endpoint, http_client)
    except Exception as ex:
        _LOG.exception(f"Error fetching google documents - {ex}")
        raise


def _sync_google_documents(connection, llm_endpoint, http_client):
    # The authorization approach is the server to server 2 legged authentication
    # we will need to find a way of saving each user's service.json file that has their credentials
    # this is the uninterrupted path but poses a risk of storing user service account details within the application
    str_folders = connection["folder_ids"]
    service_account_creds_obj = json.loads(connection["service_json_str"])

    folder_ids = str_folders.split(",")

    work_dir = f"/tmp/{uuid.uuid4()}"
    pathlib.Path(work_dir).mkdir(parents=True)
    service_account_file = os.path.join(work_dir, "service_account.json")

    with open(service_account_file, "w") as svc_file:
        svc_file.write(json.dumps(service_account_creds_obj))

    for folder_id in folder_ids:

        try:
            loader = GoogleDriveLoader(
                folder_id=folder_id,
                service_account_key=service_account_file,
                file_types=["document", "sheet", "pdf"],
                recursive=True,
            )
            documents = loader.load()
            for document in documents:
                try:
                    # get generate a file unique Id from the source metadata_value.
                    # This is supposed to be the same if source does not change
                    file_source = document.metadata["source"]
                    file_unique_id = f"{uuid.uuid5(uuid.NAMESPACE_DNS, file_source)}"

                    file_metadata = {
                        "name": document.metadata["title"],
                        "folder_id": folder_id,
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
                        llm_endpoint=llm_endpoint,
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
                        f"Done syncing file {file_metadata['name']} in location {folder_id}"
                    )
                except Exception as ex:
                    _LOG.warn(
                        f"Error when getting and ingesting file {document['metadata']['title']} - {ex}"
                    )
        except Exception as ex:
            _LOG.warn(
                f"Error when loading google files from  {folder_id} - {ex}",
                exc_info=True,
            )
    _LOG.info(f"Completed syncing to endpoint {llm_endpoint}")
