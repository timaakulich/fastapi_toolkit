import os

import pytest

os.environ.setdefault('SETTINGS_MODULE', 'tests.conf')  # noqa

from fastapi_toolkit.db import (
    BaseModel,
    create_engine,
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
