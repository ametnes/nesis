import datetime as dt

YYYY_MM_DD_HH_MM_SS = "%Y-%m-%d %H:%M:%S"
YYYYMMDDHHMMSS = "%Y%m%d%H%M%S"


def strptime(date_string: str) -> dt.datetime:
    if date_string is None:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y%m%d%H%M%S",
        "%Y-%m-%d %H:%M:%S.%f",
    ]
    for fmt in formats:
        try:
            return dt.datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    raise ValueError(
        "Date string %s does not match any of the formats %s" % (date_string, formats)
    )


def now() -> dt.datetime:
    return dt.datetime.now()
