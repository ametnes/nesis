import chardet
from pathlib import Path


def file_encoding(file_path: str, n_chars: int = 20) -> str:
    """Predict a file's encoding using chardet"""

    # Open the file as binary data
    with Path(file_path).open("rb") as f:
        # Join binary lines for specified number of lines
        rawdata = b"".join([f.read() for _ in range(n_chars)])

    return chardet.detect(rawdata)["encoding"]
