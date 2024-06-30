import logging
import tempfile
from pathlib import Path
from typing import AnyStr, BinaryIO, Dict, Any

from injector import inject, singleton

from nesis.rag.core.components.ingest.ingest_helper import IngestionHelper
from nesis.rag.core.server import ServiceException
from nesis.rag.core.settings.settings import Settings

logger = logging.getLogger(__name__)


@singleton
class ExtractService:
    @inject
    def __init__(
        self,
        settings: Settings,
    ) -> None:
        pass

    def _extract_data(
        self, file_name: str, file_data: AnyStr, metadata: dict | None = None
    ) -> list[Dict[str, Any]]:
        logger.debug("Got file data of size=%s to ingest", len(file_data))
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            try:
                path_to_tmp = Path(tmp.name)
                if isinstance(file_data, bytes):
                    path_to_tmp.write_bytes(file_data)
                else:
                    path_to_tmp.write_text(str(file_data))
                return self.extract_file(file_name, path_to_tmp, metadata)
            finally:
                tmp.close()
                path_to_tmp.unlink()

    @staticmethod
    def extract_file(
        file_name: str, file_data: Path, metadata: dict | None = None
    ) -> list[Dict[str, Any]]:
        logger.info("Ingesting file_name=%s", file_name)
        try:

            documents = IngestionHelper.transform_file_into_documents(
                file_name, file_data, metadata
            )
            logger.info(
                "Transformed file=%s into count=%s documents", file_name, len(documents)
            )

        except Exception as ex:
            raise ServiceException(ex)
        logger.info("Finished ingestion file_name=%s", file_name)
        return [document.to_dict() for document in documents]

    def extract_bin(
        self, file_name: str, raw_file_data: BinaryIO, metadata: dict | None = None
    ) -> list[Dict[str, Any]]:
        logger.debug("Extracting from binary data with file_name=%s", file_name)
        file_data = raw_file_data.read()
        return self._extract_data(file_name, file_data, metadata)
