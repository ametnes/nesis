import logging
import pathlib
import uuid
from concurrent.futures import as_completed
from datetime import datetime
from typing import Dict, Any

import memcache
import smbprotocol
from smbclient import scandir, stat, shutil

from nesis.api.core.document_loaders.loader_helper import DocumentProcessor
from nesis.api.core.models.entities import Datasource
from nesis.api.core.util import http, clean_control, isblank
from nesis.api.core.util.concurrency import IOBoundPool
from nesis.api.core.util.constants import DEFAULT_DATETIME_FORMAT, DEFAULT_SAMBA_PORT

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
        connection = self._datasource.connection
        try:
            self._sync_samba_documents(
                metadata=metadata,
            )
        except:
            _LOG.exception(f"Error syncing documents")

        try:
            self._unsync_samba_documents(
                connection=connection,
            )
        except:
            _LOG.exception(f"Error unsyncing documents")

        for future in as_completed(self._futures):
            try:
                future.result()
            except:
                _LOG.warning(future.exception())

    def _sync_samba_documents(self, metadata):

        connection = self._datasource.connection

        username = connection["user"]
        password = connection["password"]
        endpoint = connection["endpoint"]
        port = connection["port"]
        # These are any folder specified to scope the sync to
        dataobjects = connection.get("dataobjects") or ""

        dataobjects_parts = [do.strip() for do in dataobjects.split(",")]

        try:
            file_shares = scandir(
                endpoint, username=username, password=password, port=port
            )
        except Exception as ex:
            _LOG.exception(
                f"Error while scanning share on samba server {endpoint} - {ex}"
            )
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

                _metadata = {
                    **(metadata or {}),
                    "file_name": file_share.path,
                }

                self._futures.append(
                    IOBoundPool.submit(
                        self._process_file,
                        connection=connection,
                        file_share=file_share,
                        work_dir=work_dir,
                        metadata=_metadata,
                    )
                )

            except:
                _LOG.warning(
                    f"Error fetching and updating documents from shared_file share {file_share.path} - ",
                    exc_info=True,
                )

    def _process_file(self, connection, file_share, work_dir, metadata):
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
                    self._process_file(
                        connection=connection,
                        file_share=dir_file,
                        work_dir=work_dir,
                        metadata=metadata,
                    )
            return

        file_name = file_share.name
        file_stats = stat(
            file_share.path, username=username, password=password, port=port
        )
        last_change_datetime = datetime.fromtimestamp(file_stats.st_chgtime)

        try:
            file_path = f"{work_dir}/{file_share.name}"
            file_unique_id = f"{uuid.uuid5(uuid.NAMESPACE_DNS, file_share.path)}"

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
                self_link = file_share.path
                _lock_key = clean_control(f"{__name__}/locks/{self_link}")

                metadata["self_link"] = self_link

                if self._cache_client.add(key=_lock_key, val=_lock_key, time=30 * 60):
                    try:
                        self.sync(
                            endpoint,
                            file_path,
                            last_modified=last_change_datetime,
                            metadata=metadata,
                            store_metadata={
                                "shared_folder": file_share.name,
                                "file_path": file_share.path,
                                "filename": file_share.path,
                                "file_id": file_unique_id,
                                "size": file_stats.st_size,
                                "name": file_name,
                                "last_modified": last_change_datetime.strftime(
                                    DEFAULT_DATETIME_FORMAT
                                ),
                            },
                        )
                    finally:
                        self._cache_client.delete(_lock_key)
                else:
                    _LOG.info(f"Document {self_link} is already processing")

            except:
                _LOG.warning(
                    f"Failed to copy contents of shared_file {file_name} from shared location {file_share.path}",
                    exc_info=True,
                )
                return

            _LOG.info(
                f"Done syncing shared_file {file_name} in location {file_share.path}"
            )
        except Exception as ex:
            _LOG.warn(
                f"Error when getting and ingesting shared_file {file_name} - {ex}",
                exc_info=True,
            )

    def _unsync_samba_documents(self, connection):
        username = connection["user"]
        password = connection["password"]
        port = connection["port"]

        def clean(**kwargs):
            store_metadata = kwargs["store_metadata"]
            file_path = store_metadata["file_path"]
            try:
                stat(file_path, username=username, password=password, port=port)
                return False
            except Exception as error:
                if "No such file" in str(error):
                    return True
                else:
                    raise

        try:
            self.unsync(clean=clean)
        except:
            _LOG.warning("Error fetching and updating documents", exc_info=True)


def _connect_samba_server(connection):
    username = connection.get("user")
    password = connection.get("password")
    endpoint = connection.get("endpoint")
    port = connection.get("port")
    next(scandir(endpoint, username=username, password=password, port=port))


def validate_connection_info(connection: Dict[str, Any]) -> Dict[str, Any]:
    port = connection.get("port") or DEFAULT_SAMBA_PORT
    _valid_keys = ["port", "endpoint", "user", "password", "dataobjects"]
    if not str(port).isnumeric():
        raise ValueError("Port value cannot be non numeric")

    assert not isblank(
        connection.get("endpoint")
    ), "A valid share address must be supplied"

    try:
        _connect_samba_server(connection)
    except Exception as ex:
        _LOG.exception(
            f"Failed to connect to samba server at {connection['endpoint']}",
        )
        raise ValueError(ex)
    connection["port"] = port
    return {
        key: val
        for key, val in connection.items()
        if key in _valid_keys and not isblank(connection[key])
    }
