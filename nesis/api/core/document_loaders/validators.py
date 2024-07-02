from sqlalchemy import engine, create_engine

from nesis.api.core.document_loaders import samba
from nesis.api.core.document_loaders import s3
from nesis.api.core.document_loaders import minio
from nesis.api.core.document_loaders import sharepoint
from nesis.api.core.models.objects import DatasourceType


def validate_datasource_connection(datasource) -> dict:
    if datasource is None:
        raise ValueError("Invalid datasource supplied")
    source_type: str = datasource.get("type")

    if source_type is None:
        raise ValueError("source_type must be supplied")

    mode = datasource.get("mode")
    if mode not in ["ingest", "extract", None]:
        raise ValueError(f"Mode must be 'ingest' or 'extract'")

    try:
        datasource_type = DatasourceType[source_type.upper()]
    except KeyError:
        raise ValueError(f"Invalid source_type {source_type}")

    connection = datasource.get("connection")
    if connection is None:
        raise ValueError("Missing connection")

    destination_url = ((connection.get("destination") or {}).get("sql") or {}).get(
        "url"
    )
    if mode == "extract":
        if destination_url is None:
            raise ValueError("Missing url for destination target")
        else:
            try:
                _engine = create_engine(
                    url=destination_url, connect_args={"connect_timeout": 10}
                )
                with _engine.connect() as conn:
                    pass
            except Exception as ex:
                raise ValueError(f"Failed to connect to the destination - {ex}")

    match datasource_type:
        case DatasourceType.WINDOWS_SHARE:
            return samba.validate_connection_info(connection=connection)
        case DatasourceType.S3:
            return s3.validate_connection_info(connection=connection)
        case DatasourceType.MINIO:
            return minio.validate_connection_info(connection=connection)
        case DatasourceType.SHAREPOINT:
            return sharepoint.validate_connection_info(connection=connection)
        case _:
            return connection
