import pytest
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from fastapi_toolkit.db import _databases
from fastapi_toolkit.db.base import BaseModel


class User(BaseModel):
    __table_name__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))


_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
_test_session_factory = sessionmaker(
    bind=_test_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@pytest.fixture(scope="session")
def async_engine():
    return _test_engine


@pytest.fixture(scope="session")
def async_session_factory():
    return _test_session_factory


@pytest.fixture(autouse=True, scope="session")
async def setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    _databases["default"]["engine"] = _test_engine
    _databases["default"]["session"] = _test_session_factory
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    _databases["default"]["engine"] = None
    _databases["default"]["session"] = None


@pytest.fixture(autouse=True)
async def seed_data(setup_db):
    async with _test_session_factory() as session:
        users = [
            User(id=1, name="Alice", email="alice@example.com"),
            User(id=2, name="Bob", email="bob@example.com"),
            User(id=3, name="Charlie", email="charlie@test.org"),
        ]
        session.add_all(users)
        await session.commit()

    yield

    async with _test_session_factory() as session:
        await session.execute(User.__table__.delete())
        await session.commit()
