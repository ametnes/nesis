import logging
from pathlib import Path
from typing import Dict, Type

from llama_index.core import Document
from llama_index.core.readers import StringIterableReader
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.json import JSONReader
from llama_index.readers.file import (
    DocxReader,
    EpubReader,
    HWPReader,
    IPYNBReader,
    MarkdownReader,
    MboxReader,
    PandasCSVReader,
    PDFReader,
    PptxReader,
    VideoAudioReader,
)  # pants: no-infer-dep

from nesis.rag.core.components.ingest.readers import (
    ExcelReader,
    TiffReader,
    OdsReader,
    ImageReader,
    PdfReader,
)

logger = logging.getLogger(__name__)


FILE_READER_CLS: Dict[str, Type[BaseReader]] = {
    ".hwp": HWPReader,
    ".pdf": PdfReader,
    ".doc": DocxReader,
    ".docx": DocxReader,
    ".pptx": PptxReader,
    ".ppt": PptxReader,
    ".pptm": PptxReader,
    ".jpg": ImageReader,
    ".png": ImageReader,
    ".jpeg": ImageReader,
    ".mp3": VideoAudioReader,
    ".mp4": VideoAudioReader,
    ".csv": PandasCSVReader,
    ".epub": EpubReader,
    ".md": MarkdownReader,
    ".mbox": MboxReader,
    ".ipynb": IPYNBReader,
    ".json": JSONReader,
    ".xls": ExcelReader,
    ".xlsx": ExcelReader,
    ".ods": OdsReader,
    ".tiff": TiffReader,
}


class IngestionHelper:
    """Helper class to transform a file into a list of documents.

    This class should be used to transform a file into a list of documents.
    These methods are thread-safe (and multiprocessing-safe).
    """

    @staticmethod
    def transform_file_into_documents(
        file_name: str, file_data: Path, metadata: dict | None
    ) -> list[Document]:
        documents = IngestionHelper._load_file_to_documents(file_name, file_data)
        for document in documents:
            document.metadata["file_name"] = file_name
            document.metadata = {**document.metadata, **(metadata or {})}
        IngestionHelper._exclude_metadata(documents)
        return documents

    @staticmethod
    def _load_file_to_documents(file_name: str, file_data: Path) -> list[Document]:
        logger.debug("Transforming file_name=%s into documents", file_name)
        extension = Path(file_name).suffix
        reader_cls = FILE_READER_CLS.get(extension.lower())
        if reader_cls is None:
            logger.debug(
                "No reader found for extension=%s, using default string reader",
                extension,
            )
            # Read as a plain text
            string_reader = StringIterableReader()
            return string_reader.load_data([file_data.read_text()])

        logger.debug("Specific reader found for extension=%s", extension)
        return reader_cls().load_data(file_data)

    @staticmethod
    def _exclude_metadata(documents: list[Document]) -> None:
        logger.debug("Excluding metadata from count=%s documents", len(documents))
        for document in documents:
            document.metadata["doc_id"] = document.doc_id
            # We don't want the Embeddings search to receive this metadata
            document.excluded_embed_metadata_keys = ["doc_id"]
            # We don't want the LLM to receive these metadata in the context
            document.excluded_llm_metadata_keys = ["file_name", "doc_id", "page_label"]
