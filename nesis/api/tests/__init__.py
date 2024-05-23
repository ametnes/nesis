import json
import pathlib
from typing import Dict, Any
from tzlocal import get_localzone

import pandas as pd
from sqlalchemy import text
import os

from nesis.api.core.models.entities import (
    Rule,
    Prediction,
    Model,
    Setting,
    Role,
    User,
    Datasource,
    Document,
    Task,
    App,
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
    "rag": {"endpoint": "http://localhost:8080"},
    "memcache": {
        "hosts": [os.environ.get("NESIS_MEMCACHE_HOSTS", "127.0.0.1:11211")],
        "session": {"expiry": 0},
        "cache": {
            "timeout_default": 300,
        },
    },
    "tasks": {
        "job": {
            "stores": {
                "url": os.environ.get(
                    "NESIS_API_TASKS_JOB_STORES_URL",
                    os.environ.get(
                        "NESIS_API_DATABASE_URL",
                        "postgresql://postgres:password@localhost:65432/nesis",
                    ),
                )
            },
            "defaults": {
                "coalesce": True,
                "max_instances": 3,
                "misfire_grace_time": 60,
            },
        },
        "timezone": os.environ.get("NESIS_API_TASKS_TIMEZONE", str(get_localzone())),
        "executors": {"default_size": 30, "pool_size": 3},
    },
}


def get_header(token=None):
    header = {"Content-Type": "application/json"}
    if token:
        header["Authorization"] = "Bearer %s" % token
    return header


def clear_database(session):
    session.query(Rule).delete()
    session.query(Model).delete()
    session.query(Prediction).delete()
    session.query(Setting).delete()
    session.query(User).delete()
    session.query(Role).delete()
    session.query(Datasource).delete()
    session.query(Document).delete()
    session.query(Task).delete()
    session.query(App).delete()
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


def get_admin_session(app) -> Dict[str, Any]:
    admin_data = {
        "password": admin_password,
        "email": admin_email,
    }
    return app.post(
        f"/v1/sessions", headers=get_header(), data=json.dumps(admin_data)
    ).json


def get_user_session(client, session, roles) -> Dict[str, Any]:
    payload = {
        "name": "The User",
        "email": "the.user@domain.com",
        "password": "password",
        "roles": roles,
    }

    response = client.post(
        f"/v1/users",
        headers=get_header(token=session["token"]),
        data=json.dumps(payload),
    )
    assert 200 == response.status_code, response.text

    return client.post(
        f"/v1/sessions", headers=get_header(), data=json.dumps(payload)
    ).json


def create_role(client, session: dict, role: dict, expect=200) -> Dict[str, Any]:

    response = client.post(
        f"/v1/roles", headers=get_header(token=session["token"]), data=json.dumps(role)
    )
    assert expect == response.status_code, response.text
    return response.json


def create_datasource(client, session, datasource, expected=200):

    response = client.post(
        f"/v1/datasources",
        headers=get_header(token=session["token"]),
        data=json.dumps(datasource),
    )
    assert expected == response.status_code, response.text
    return response.json
