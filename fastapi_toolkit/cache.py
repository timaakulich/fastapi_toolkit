import asyncio
import pickle
import time
from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

T = TypeVar("T")


class SecretCacheBackend(ABC, Generic[T]):
    def __init__(self) -> None:
        self._initialized = False
        self._init_lock = asyncio.Lock()

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def init(self, dsn: str | None = None) -> None:
        async with self._init_lock:
            if self._initialized:
                return
            await self._init(dsn)
            self._initialized = True

    async def _init(self, dsn: str | None = None) -> None:
        return

    @abstractmethod
    async def get(self, key: str) -> T | None: ...

    @abstractmethod
    async def set(self, key: str, value: T, ttl: int) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class InMemoryBackend(SecretCacheBackend[T]):
    def __init__(self) -> None:
        super().__init__()
        self._initialized = True
        self._store: dict[str, tuple[T, int]] = {}

    async def get(self, key: str) -> T | None:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at < int(time.time()):
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: T, ttl: int) -> None:
        self._store[key] = (value, int(time.time()) + ttl)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisBackend(SecretCacheBackend[T]):
    prefix: ClassVar[str] = "fastapi_toolkit:secret:"

    def __init__(self) -> None:
        try:
            import redis.asyncio  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "redis is required for RedisBackend. "
                "Install it with: pip install fastapi-toolkit[redis]",
            ) from exc
        super().__init__()
        self._client: redis.asyncio.Redis | None = None

    async def _init(self, dsn: str | None = None) -> None:
        import redis.asyncio
        self._client = redis.asyncio.Redis.from_url(dsn)

    async def get(self, key: str) -> T | None:
        raw = await self._client.get(self._key(key))
        if raw is None:
            return None
        return pickle.loads(raw)

    async def set(self, key: str, value: T, ttl: int) -> None:
        await self._client.set(self._key(key), pickle.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        await self._client.delete(self._key(key))

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"
