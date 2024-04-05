import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

DBSession = scoped_session(sessionmaker())
Base = declarative_base()


def initialize_engine(config):
    app_config = config.get("database") or {}

    database_url: str = app_config.get("url", os.environ.get("NESIS_API_DATABASE_URL"))
    engine = create_engine(
        database_url,
        echo=app_config.get("debug", False),
        pool_pre_ping=True,
        pool_size=app_config.get("pool_size", 20),
        max_overflow=app_config.get("max_overflow", 0),
    )

    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    if app_config.get("create", False):
        Base.metadata.create_all(engine)

    return engine
