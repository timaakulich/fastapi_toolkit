import os

import pytest

from tests.mixer import AsyncMixer

os.environ.setdefault('SETTINGS_MODULE', 'tests.conf')  # noqa

from fastapi_toolkit.db import (
    BaseModel,
    create_engine,
    create_session,
)
from tests.models import *  # noqa


@pytest.fixture
async def db():
    engine = create_engine()

    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.create_all)

    yield

    async with engine.begin() as connection:
        await connection.run_sync(BaseModel.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def mixer(db):
    async with create_session() as session:
        yield AsyncMixer(session)
