from unittest.mock import AsyncMock

from fastapi_toolkit.db import async_session


class TestAsyncSession:
    async def test_reuses_existing_session(self):
        mock_session = AsyncMock()
        async with async_session(mock_session) as session:
            assert session is mock_session

    async def test_creates_new_session(self):
        async with async_session() as session:
            assert session is not None
