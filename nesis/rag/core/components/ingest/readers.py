import pathlib
import tempfile
from pathlib import Path
from typing import List, Optional, Dict

from fsspec import AbstractFileSystem
from llama_index.core.readers.base import BaseReader
import pandas as pd
from llama_index.core import Document

from PIL import Image, ImageSequence
import os
import os.path
import glob
from llama_index.readers.file import ImageReader


class ExcelReader(BaseReader):
    """
    A simple MS Excel file reader. Uses pandas in the background
    """

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        data = pd.read_excel(file.absolute()).to_string()
        return [Document(text=data, metadata=extra_info or {})]


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


class TiffReader(BaseReader):
    """
    A simple tiff file reader. Converts the pages into png and then uses an image reader to convert into llama-index
    documents
    """

    @staticmethod
    def _load_page_data(
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:
        return ImageReader().load_data(file.absolute(), extra_info=extra_info, fs=fs)

    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        fs: Optional[AbstractFileSystem] = None,
    ) -> List[Document]:

        im = Image.open(file.absolute())
        documents: List[Document] = []
        for idx, page in enumerate(ImageSequence.Iterator(im)):
            temp_file_name = tempfile.NamedTemporaryFile(
                dir=tempfile.gettempdir(), prefix=f"{file.name.split('.')[0]}-{idx}-"
            )
            path = pathlib.Path(temp_file_name.name).with_suffix(".png")

            page.save(path)
            page_documents: List[Document] = self._load_page_data(
                file=path, extra_info=extra_info, fs=fs
            )
            documents += page_documents

        return documents
