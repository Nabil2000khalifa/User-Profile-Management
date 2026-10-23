from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import Settings, get_settings


@lru_cache
def get_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def get_configured_engine(settings: Settings | None = None) -> Engine:
    configured_settings = settings or get_settings()
    return get_engine(configured_settings.database_url.get_secret_value())


def get_db_session() -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=get_configured_engine(), autoflush=False)
    with session_factory() as session:
        yield session


def check_database_connection(engine: Engine) -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True
