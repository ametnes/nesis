import datetime as dt


def strptime(date_string: str) -> dt.datetime:
    formats = {"%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"}
    for fmt in formats:
        try:
            return dt.datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    raise ValueError(
        "Date string %s does not match any of the formats %s" % (date_string, formats)
    )
