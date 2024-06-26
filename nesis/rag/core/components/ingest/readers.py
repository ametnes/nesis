import copy
import pathlib
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
from PIL import Image, ImageSequence
from fsspec import AbstractFileSystem
from llama_index.core import Document
from llama_index.core.readers.base import BaseReader
from unstructured.documents.elements import Element
from unstructured.partition.image import partition_image
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.xlsx import partition_xlsx


def _clean_metadata(metadata: Dict, exclusion_list: List[str] = None) -> Dict:
    """
    We want to remove any unwanted metadata fields. This is particularly useful when readers introduce metadata from
    intermediate steps, but we would rather not have that metadata in the vector store.
    :param metadata: the metadata to clean
    :param exclusion_list: the exclusion field list
    :return: the cleaned metadata
    """
    metadata_copy = copy.deepcopy(metadata or {})
    for metadata_item in list(metadata_copy.keys()):
        metadata_value = metadata_copy.get(metadata_item)
        if metadata_value is None:
            continue
        if isinstance(metadata_value, dict):
            _clean_metadata_item = _clean_metadata(metadata_value, exclusion_list)
            metadata_copy[metadata_item] = _clean_metadata_item
        else:
            for exclusion_item in exclusion_list or []:
                metadata_copy.pop(exclusion_item, None)
    return metadata_copy


class BaseFileReader(BaseReader):
    """
    A simple PDF file reader.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or {}
        self._metadata_exclusion_list: list[str] = (
            self._config.get("metadata_exclusion_list")
            or [
                "file_directory",
                "filename",
            ]
        ) + [
            "text",
            "file_name",
            "coordinates",
            "embedding",
            "metadata_template",
            "metadata_seperator",
            "text_template",
            "excluded_embed_metadata_keys",
            "excluded_llm_metadata_keys",
            "relationships",
            "start_char_idx",
            "end_char_idx",
        ]

    def load_documents(
        self,
        elements: List[Element],
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        documents: List[Document] = []

        for element in elements:
            element_dict = element.to_dict()
            if element_dict["text"] == "":
                continue
            element_text = element_dict["text"]
            metadata = _clean_metadata(
                {
                    **{
                        key: val
                        for key, val in element_dict.items()
                        if key not in ["text", "metadata"]
                    },
                    **element_dict["metadata"],
                },
                exclusion_list=self._metadata_exclusion_list,
            )
            document = Document(
                text=element_text,
                metadata={
                    **(extra_info or {}),
                    **metadata,
                },
            )
            documents.append(document)
        return documents


class ExcelReader(BaseFileReader):

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        BaseFileReader.__init__(self, config=config)

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        elements = partition_xlsx(file.absolute())
        return self.load_documents(elements=elements, extra_info=extra_info)


class OdsReader(BaseReader):
    """
    A simple open document spreadsheet reader
    """

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        data = pd.read_excel(file.absolute(), engine="odf").to_string()
        return [Document(text=data, metadata=extra_info or {})]


class ImageReader(BaseFileReader):
    """
    The llamaindex reader doesn't return any text, so we use unstructured.io instead.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        BaseFileReader.__init__(self, config=config)

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        elements = partition_image(
            file.absolute(), strategy="hi_res", infer_table_structure=True
        )
        return self.load_documents(elements=elements, extra_info=extra_info)


class TiffReader(BaseReader):
    """
    A simple tiff file reader. Converts the pages into png and then uses an image reader to convert into llama-index
    documents
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config
        self._image_reader = ImageReader(config=self._config)

    def _load_page_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        return self._image_reader.load_data(
            file.absolute(), extra_info=extra_info, fs=fs
        )

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:

        with Image.open(file.absolute()) as image:
            documents: List[Document] = []
            for idx, page in enumerate(ImageSequence.Iterator(image)):
                with tempfile.NamedTemporaryFile(
                    dir=tempfile.gettempdir(),
                    prefix=f"{file.name.split('.')[0]}-{idx}-",
                ) as temp_file_name:
                    path = pathlib.Path(temp_file_name.name).with_suffix(".png")

                    page.save(path)
                    page_documents: List[Document] = self._load_page_data(
                        file=path, extra_info=extra_info, fs=fs
                    )
                    documents += page_documents

        return documents


class PdfReader(BaseFileReader):
    """
    A simple PDF file reader.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        BaseFileReader.__init__(self, config=config)

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        elements = partition_pdf(
            file.absolute(), strategy="hi_res", infer_table_structure=True
        )
        return self.load_documents(elements=elements, extra_info=extra_info)
