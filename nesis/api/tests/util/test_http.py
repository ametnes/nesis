import json
import pathlib
import unittest
import unittest.mock as mock

import pytest

from nesis.api import tests
import nesis.api.core.util.http as http


@pytest.fixture
def ut():
    return unittest.TestCase()


@mock.patch("nesis.api.core.util.http.req")
def test_upload(requests: mock.MagicMock, ut: unittest.TestCase) -> None:
    file_path = (
        pathlib.Path(tests.__file__).parent.absolute() / "resources/samplepptx.pptx"
    )
    client = http.HttpClient(config=tests.config)

    url = "http://localhost:8080/v1/ingest/files"
    metadata = {
        "datasource": "datasource",
        "file_name": str(file_path.absolute()),
        "self_link": str(file_path.absolute()),
    }

    client.upload(url=url, filepath=file_path, field="file", metadata=metadata)
    _, post_kwargs = requests.post.call_args_list[0]

    assert post_kwargs["url"] == url
    ut.assertDictEqual(json.loads(post_kwargs["params"]["metadata"]), metadata)
    ut.assertDictEqual(json.loads(post_kwargs["data"]["metadata"]), metadata)
