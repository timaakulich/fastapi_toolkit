# Standard Library
from contextlib import asynccontextmanager

# Third Party Library
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

__all__ = (
    "async_session",
    "create_engine",
    "init_db",
)

_databases: dict[str, dict] = {
    "default": {
        "engine": None,
        "session": None,
    },
}


def create_engine(
    database_dsn: PostgresDsn,
    database: str = "default",
    engine_kwargs: dict | None = None,
) -> AsyncEngine:
    global _databases
    _databases.setdefault(database, {"engine": None, "session": None})
    if not _databases[database]["engine"]:
        _databases[database]["engine"] = create_async_engine(
            database_dsn,
            pool_pre_ping=True,
            **(engine_kwargs or {}),
        )

    return _databases[database]["engine"]


def init_db(
    database_dsn: PostgresDsn,
    database: str = "default",
    engine_kwargs: dict | None = None,
    session_maker_kwargs: dict | None = None,
):
    _engine: AsyncEngine | None = create_engine(database_dsn, database, engine_kwargs)
    global _databases

    if not _databases[database]["session"]:
        _databases[database]["session"] = sessionmaker(
            bind=_engine,
            expire_on_commit=False,
            class_=AsyncSession,
            **(session_maker_kwargs or {}),
        )


@asynccontextmanager
async def async_session(exists_session=None, database="default", **kwargs):
    if exists_session:
        yield exists_session
    else:
        global _databases
        _session_cls = _databases[database]["session"]
        async with _session_cls(**kwargs) as session:
            yield session
