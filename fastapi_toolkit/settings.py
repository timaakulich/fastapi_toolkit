import asyncio
import json
from typing import Annotated, Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, BeforeValidator, Field, PrivateAttr, SecretStr
from pydantic_settings import BaseSettings as PydanticSettings
from pydantic_settings import SettingsConfigDict

from fastapi_toolkit.cache import InMemoryBackend, SecretCacheBackend

settings_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    env_prefix="app_",
    extra="allow",
    env_nested_delimiter="__",
)


class SecretSettings(PydanticSettings):
    model_config = settings_config

    @classmethod
    def load_secret(
            cls,
            secret_name: str,
            region: str,
            endpoint_url: str | None = None,
            aws_access_key_id: str | None = None,
            aws_secret_access_key: str | None = None,
    ) -> tuple["SecretSettings", bool]:
        try:
            import botocore.session
        except ImportError as exc:
            raise ImportError(
                "botocore is required for AWS Secrets Manager support. "
                "Install it with: pip install fastapi-toolkit[aws]"
            ) from exc
        session = botocore.session.get_session()
        client = session.create_client(
            "secretsmanager",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        _settings = cls()
        try:
            response = client.get_secret_value(SecretId=secret_name)
        except Exception as exc:
            logger.warning("Can not load secret {}. Reason: {}", secret_name, exc)
            return _settings, False
        secret_string = response["SecretString"]
        secret = json.loads(secret_string)
        logger.info("Load secret {}.", secret_name)
        loaded_secret = {}
        for key in secret:
            name = key.replace(cls.model_config["env_prefix"], "", 1)
            try:
                loaded_secret[name] = json.loads(secret[key])
            except Exception:
                loaded_secret[name] = secret[key]
        _secret_settings = cls.model_validate(loaded_secret)
        for key in _settings.model_dump():
            setattr(_settings, key, getattr(_secret_settings, key))
        return _settings, True

    def save_secret(
            self,
            secret_name: str,
            region: str,
            endpoint_url: str | None = None,
            aws_access_key_id: str | None = None,
            aws_secret_access_key: str | None = None,
    ) -> None:
        try:
            import botocore.session
        except ImportError as exc:
            raise ImportError(
                "botocore is required for AWS Secrets Manager support. "
                "Install it with: pip install fastapi-toolkit[aws]",
            ) from exc
        session = botocore.session.get_session()
        client = session.create_client(
            "secretsmanager",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        prefix = self.model_config["env_prefix"]
        payload = {}
        for key, value in self.model_dump(exclude_unset=True).items():
            if isinstance(value, SecretStr):
                value = value.get_secret_value()
            if isinstance(value, set | frozenset):
                value = list(value)
            if isinstance(value, dict | list):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = json.dumps(value)
            payload[f"{prefix}{key}"] = value
        client.put_secret_value(
            SecretId=secret_name, SecretString=json.dumps(payload),
        )
        logger.info("Save secret {}.", secret_name)


class GitSettings(BaseModel):
    hash: str = None
    branch: str = None


T = TypeVar("T", bound=SecretSettings)


class BaseSettings(PydanticSettings, Generic[T]):
    model_config = SettingsConfigDict(
        **settings_config,
        arbitrary_types_allowed=True,
    )

    project: str
    environment: str
    region: str

    cache_ttl: int = 5 * 60
    git: GitSettings = GitSettings()

    secret_model: type[T]
    secret_cache: SecretCacheBackend = Field(default_factory=InMemoryBackend)
    secret_cache_dsn_key: str | None = None

    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_endpoint_url: str | None = None

    _update_lock: asyncio.Lock | None = PrivateAttr(default_factory=asyncio.Lock)

    @property
    def secret_name(self):
        return f"{self.environment}/{self.project}"

    async def get_secret(self) -> T:
        cached = None
        if self.secret_cache.is_initialized:
            cached = await self.secret_cache.get(self.secret_name)
        if cached is not None:
            return cached
        value, _ = await asyncio.to_thread(
            self.secret_model.load_secret,
            self.secret_name, self.region,
            self.aws_endpoint_url, self.aws_access_key_id,
            self.aws_secret_access_key
        )
        if not self.secret_cache.is_initialized:
            secret_dsn = getattr(value, self.secret_cache_dsn_key, None) if self.secret_cache_dsn_key else None
            await self.secret_cache.init(secret_dsn.get_secret_value() if isinstance(secret_dsn, SecretStr) else secret_dsn)
        await self.secret_cache.set(self.secret_name, value, self.cache_ttl)
        return value

    async def invalidate_secret(self) -> None:
        if self.secret_cache.is_initialized:
            await self.secret_cache.delete(self.secret_name)

    async def update_secret(self, **kwargs) -> T:
        async with self._update_lock:
            current = await self.get_secret()
            data = {
                k: v.get_secret_value() if isinstance(v, SecretStr) else v
                for k, v in current.model_dump().items()
            }
            data.update(kwargs)
            updated = self.secret_model.model_validate(data)
            await asyncio.to_thread(
                updated.save_secret, self.secret_name, self.region,
                self.aws_endpoint_url, self.aws_access_key_id,
                self.aws_secret_access_key,
            )
            await self.invalidate_secret()
            return updated


def escape_string(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("\\t", "\t").replace("\\n", "\n")


EscapedSecretStr = Annotated[SecretStr, BeforeValidator(escape_string)]
