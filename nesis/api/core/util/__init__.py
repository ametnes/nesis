import hashlib
import re

from sqlalchemy import text


def merge(source, destination):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination


def clean_control(value: str) -> str:
    return re.sub(r"[ \\/,:.]+", "", value)


def uid(value: str) -> str:
    h = hashlib.sha3_512()
    h.update(value.encode("utf-8"))
    return h.hexdigest()


def run_sql(engine, path):
    with engine.connect() as con:
        with open(path) as file:
            query = text(file.read())
            con.execute(query)
