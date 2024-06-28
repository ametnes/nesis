import pathlib
import pandas as pd
from sqlalchemy import text
import os

from nesis.api.core.models.entities import (
    Prediction,
    Setting,
    Role,
    User,
    Datasource,
    Document,
)

os.environ["PGPT_PROFILES"] = "test"
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
admin_email = "test.user@domain.com"
admin_password = "password"
os.environ["NESIS_ADMIN_EMAIL"] = admin_email
os.environ["NESIS_ADMIN_PASSWORD"] = admin_password

config = {
    "database": {
        "url": os.environ.get(
            "NESIS_API_DATABASE_URL",
            "postgresql://postgres:password@localhost:65432/nesis",
        ),
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "65432"),
        "user": os.environ.get("POSTGRES_USER", "admin"),
        "password": os.environ.get("POSTGRES_PASSWORD", "password"),
        "name": os.environ.get("POSTGRES_DB", "nesis"),
        "debug": False,
        "create": True,
    },
    "modules": {
        "data": {"llm": {}},
        "qanda": {"endpoint": "http://localhost:9080"},
    },
    "datasource": {
        "url": os.environ.get(
            "POSTGRES_DS_DB_URL", "postgresql://admin:password@postgres11:5432/nesis"
        ),
        "host": os.environ.get("POSTGRES_DS_HOST", "postgres11"),
        "port": os.environ.get("POSTGRES_DS_PORT", "5432"),
        "user": "admin",
        "password": "password",
        "db": "nesis",
    },
    "memcache": {
        "hosts": [os.environ.get("NESIS_MEMCACHE_HOSTS", "127.0.0.1:11211")],
        "session": {"expiry": 0},
        "cache": {
            "timeout_default": 300,
        },
    },
}


def get_header(token=None):
    header = {"Content-Type": "application/json"}
    if token:
        header["Authorization"] = "Bearer %s" % token
    return header


def clear_database(session):
    session.query(Prediction).delete()
    session.query(Setting).delete()
    session.query(User).delete()
    session.query(Role).delete()
    session.query(Datasource).delete()
    session.query(Document).delete()
    session.commit()


def load_test_data(connection):
    with open(
        f"{pathlib.Path(__file__).parent.absolute()}/customer-train.csv", "r"
    ) as file:
        data_df = pd.read_csv(file)
    data_df.to_sql("customer", con=connection, index=False, if_exists="replace")


def run_sql(engine, path):
    with engine.connect() as con:
        with open(path) as file:
            query = text(file.read() + "\n\n" + "COMMIT;")
            con.execute(query)
