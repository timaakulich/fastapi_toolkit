from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from fastapi_toolkit.conf import settings
from fastapi_toolkit.db.base_class import BaseModel

__all__ = (
    'create_session',
    'BaseModel',
    'init_db'
)


_engine = None
_Session: sessionmaker


def init_db():
    global _engine
    if _engine:
        return
    global _Session
    _engine = create_async_engine(
        settings.database_dsn,
        pool_pre_ping=True
    )
    _Session = sessionmaker(
        # autocommit=False,
        # autoflush=False,
        bind=_engine,
        expire_on_commit=False,
        class_=AsyncSession
    )


@asynccontextmanager
async def create_session():
    init_db()
    async with _Session() as session:  # noqa
        yield session
