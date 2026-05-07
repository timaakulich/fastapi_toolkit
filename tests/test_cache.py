import pickle
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi_toolkit.cache import InMemoryBackend, RedisBackend


class TestInMemoryBackend:
    async def test_is_initialized(self):
        backend = InMemoryBackend()
        assert backend.is_initialized is True

    async def test_get_miss(self):
        backend = InMemoryBackend()
        assert await backend.get("k") is None

    async def test_set_and_get(self):
        backend = InMemoryBackend()
        await backend.set("k", "v", ttl=60)
        assert await backend.get("k") == "v"

    async def test_expiry(self):
        backend = InMemoryBackend()
        await backend.set("k", "v", ttl=60)
        with patch("fastapi_toolkit.cache.time.time", return_value=time.time() + 120):
            assert await backend.get("k") is None

    async def test_delete(self):
        backend = InMemoryBackend()
        await backend.set("k", "v", ttl=60)
        await backend.delete("k")
        assert await backend.get("k") is None

    async def test_delete_missing(self):
        backend = InMemoryBackend()
        await backend.delete("k")


class TestRedisBackend:
    async def test_init_creates_client(self):
        backend = RedisBackend()
        assert backend.is_initialized is False
        fake_client = AsyncMock()
        with patch("redis.asyncio.Redis") as redis_cls:
            redis_cls.from_url = MagicMock(return_value=fake_client)
            await backend.init("redis://localhost:6379/0")
        assert backend.is_initialized is True
        assert backend._client is fake_client
        redis_cls.from_url.assert_called_once_with("redis://localhost:6379/0")

    async def test_init_idempotent(self):
        backend = RedisBackend()
        with patch("redis.asyncio.Redis") as redis_cls:
            redis_cls.from_url = MagicMock(return_value=AsyncMock())
            await backend.init("redis://h")
            await backend.init("redis://h")
            assert redis_cls.from_url.call_count == 1

    async def test_get_miss(self):
        backend = RedisBackend()
        client = AsyncMock()
        client.get.return_value = None
        backend._client = client
        backend._initialized = True
        assert await backend.get("k") is None
        client.get.assert_awaited_once_with("fastapi_toolkit:secret:k")

    async def test_set(self):
        backend = RedisBackend()
        client = AsyncMock()
        backend._client = client
        backend._initialized = True
        await backend.set("k", {"a": 1}, ttl=30)
        client.set.assert_awaited_once_with(
            "fastapi_toolkit:secret:k", pickle.dumps({"a": 1}), ex=30,
        )

    async def test_get_hit(self):
        backend = RedisBackend()
        client = AsyncMock()
        client.get.return_value = pickle.dumps({"a": 1})
        backend._client = client
        backend._initialized = True
        assert await backend.get("k") == {"a": 1}

    async def test_delete(self):
        backend = RedisBackend()
        client = AsyncMock()
        backend._client = client
        backend._initialized = True
        await backend.delete("k")
        client.delete.assert_awaited_once_with("fastapi_toolkit:secret:k")

    def test_missing_redis(self):
        with patch.dict("sys.modules", {"redis": None, "redis.asyncio": None}):
            with pytest.raises(ImportError, match="redis is required"):
                RedisBackend()
