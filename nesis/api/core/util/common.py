import json
import uuid
from flask import abort

from nesis.api.core.util.constants import (
    CACHE_SEPARATOR,
    BEARER_PREFIX,
    BASIC_PREFIX,
)

json_headers = {"Content-Type": "application/json", "Accept": "application/json"}


def get_param_value(param):
    if type(param) is list:
        return param[0]
    else:
        return param


def string2boolean(str_val):
    if str_val and str_val.lower() in ["y", "yes", "true", "t", "1"]:
        return True
    else:
        return False


def get_short_id(num_chars=10):
    unique_id = str(uuid.uuid4()).replace("-", "")
    return unique_id[:num_chars]


def create_cache_key(path, params):
    key = path + CACHE_SEPARATOR + json.dumps(params, sort_keys=True)
    key = key.replace(" ", "")
    return key


def set_in_cache(cache_client, config, key, value, timeout=None):
    # use default if timeout not supplied
    if not timeout:
        try:
            timeout = config["memcache"]["cache"]["timeout_default"]
        except Exception:
            timeout = 300

    cache_client.set(key, value, time=timeout)


def get_from_cache(cache_client, key):
    return cache_client.get(key)


def delete_from_cache(cache_client, config, list_key):
    keys = cache_client.get(list_key) or set()
    cache_client.delete_multi(keys)
    cache_client.set(list_key, set())


def update_cached_keys(cache_client, list_key, cache_composite_key):
    cached_keys = cache_client.get(list_key) or set()
    cached_keys.add(cache_composite_key)
    cache_client.set(list_key, cached_keys)
    return cached_keys


def get_bearer_token(header):
    if not header:
        return None

    auth_type, _, token = header.partition(" ")

    # bearer auth using sessions
    if auth_type == BEARER_PREFIX:
        try:
            return token.strip()
        except:
            return None

    # basic auth using PAT
    elif auth_type == BASIC_PREFIX:
        return token

    else:
        abort(401)


def get_client_ip(request):
    try:
        return (
            request.environ.get("HTTP_X_FORWARDED_FOR")
            or request.environ.get("REMOTE_ADDR")
            or request.remote_addr
        )
    except Exception:
        return None


def resource_api_headers(token):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    return headers
