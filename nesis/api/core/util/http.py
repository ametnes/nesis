import json
import pathlib
import base64
from typing import Union

import memcache
import requests as req
import logging


class HttpClient(object):
    """
    A simple http client wrapping the request library
    """

    def __init__(self, config=None):
        self._config = config
        self._cache = memcache.Client(config["memcache"]["hosts"], debug=1)
        self._LOG = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def get(self, url, params=None, headers=None, cookies=None, auth=None) -> str:
        with req.session() as session:
            _headers = headers or {}
            if auth:
                b64bytes = base64.b64encode(f"{auth[0]}:{auth[0]}".encode("utf-8"))
                userpass_encoded = "Basic " + str(b64bytes, "utf-8")
                _headers["Authorization"] = str(userpass_encoded)
                session.headers = _headers

            response = session.get(
                url,
                params=params,
                allow_redirects=True,
                cookies=cookies,
                auth=(auth[0], auth[1]),
            )
            if response.ok:
                return response.text
            raise Exception(response.text)

    def delete(self, url, params=None, headers=None, cookies=None) -> str:
        with req.Session() as s:
            response = s.delete(
                url,
                params=params,
                headers=headers,
                allow_redirects=True,
                cookies=cookies,
            )
            if response.ok:
                return response.text
            raise Exception(response.text)

    def post(self, url, payload, headers=None, cookies=None) -> str:
        with req.Session() as s:
            response = s.post(
                url,
                headers=headers,
                allow_redirects=True,
                data=payload,
                cookies=cookies,
            )
            if response.ok:
                return response.text
            raise Exception(response.text)

    def put(self, url, payload, headers=None, cookies=None) -> str:
        with req.Session() as s:
            response = s.put(
                url,
                headers=headers,
                allow_redirects=True,
                data=payload,
                cookies=cookies,
            )
            if response.ok:
                return response.text
            raise Exception(response.text)

    def upload(self, url, filepath, field, metadata: dict) -> Union[None, str]:
        """
        Upload a file. We ensure that it is threadsafe by locking on the self_link using Memcached's add method.
        """

        self_link = metadata.get("self_link")
        if self_link is None:
            raise ValueError("Invalid metadata. Must have a self_link link")
        datasource = metadata.get("datasource")
        if datasource is None:
            raise ValueError("Invalid metadata. Must have a datasource")

        """
        Here we use memcached add function to simulate locking. This ensure that if multiple instances of this application
        are running, there will not be a conflict on which instance processed the file
        """
        if self._cache.add(key=self_link, val=self_link, time=30 * 60):
            try:
                with open(filepath, "rb") as file_handle:
                    file_name = pathlib.Path(filepath).name
                    _metadata = json.dumps(metadata)
                    multipart_form_data = {field: (file_name, file_handle)}

                    data = {"metadata": _metadata}

                    response = req.post(
                        url=url, files=multipart_form_data, params=data, data=data
                    )
                    match response.status_code:
                        case 400:
                            # ValueError is fitting since 400 means the data we sent is invalid
                            raise ValueError(response.text)
                        case 500 | 501 | 503:
                            response.raise_for_status()
                    return response.text
            finally:
                self._cache.delete(self_link)
        else:
            raise UserWarning(f"File {filepath} is already processing")
