from datetime import datetime

import pytest

from nesis.api.core.util import clean_control
from nesis.api.core.util import dateutil as du


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            "minio/locks/http://localhost:59000//boe/Introduction to Nesis-C.mp4",
            "miniolockshttplocalhost59000boeIntroductiontoNesis-Cmp4",
        ),
        (
            "\\samba\localhost:59000//boe/Introduction to Nesis-C.mp4",
            "sambalocalhost59000boeIntroductiontoNesis-Cmp4",
        ),
    ],
)
def test_upload(value, expected) -> None:
    result = clean_control(value=value)
    assert result == expected


def test_strptime() -> None:
    dt = du.strptime("2024-04-22 08:30:28+00:00")
    assert isinstance(dt, datetime)
