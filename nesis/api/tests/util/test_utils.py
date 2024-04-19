import pytest

from nesis.api.core.util import clean_control


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
