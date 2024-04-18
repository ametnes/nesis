import json
import pathlib
import unittest
import unittest.mock as mock

import pytest

from nesis.api import tests
import nesis.api.core.util.http as http
from nesis.api.core.util import clean_control


@pytest.mark.parametrize(
    "value, expected",
    [
        ("minio/locks/http://localhost:59000//boe/Introduction to Nesis-C.mp4", ""),
        ("\\samba\localhost:59000//boe/Introduction to Nesis-C.mp4", ""),
    ],
)
def test_upload(value, expected) -> None:
    print(clean_control(value=value))
