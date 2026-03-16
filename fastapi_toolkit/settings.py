import asyncio
import json
import time
from typing import Annotated, Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, BeforeValidator, SecretStr
from pydantic_settings import BaseSettings as PydanticSettings
from pydantic_settings import SettingsConfigDict

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
    def load_secret(cls, secret_name, region) -> tuple["SecretSettings", bool]:
        try:
            import botocore.session
        except ImportError as exc:
            raise ImportError(
                "botocore is required for AWS Secrets Manager support. "
                "Install it with: pip install fastapi-toolkit[aws]"
            ) from exc
        session = botocore.session.get_session()
        client = session.create_client("secretsmanager", region_name=region)
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


class GitSettings(BaseModel):
    hash: str = None
    branch: str = None


T = TypeVar("T", bound=SecretSettings)


class BaseSettings(PydanticSettings, Generic[T]):
    model_config = settings_config

    project: str
    environment: str
    region: str

    cache_ttl: int = 5 * 60
    git: GitSettings = GitSettings()

    cached_secret: tuple[SecretSettings | None, int] = (None, 0)
    secret_model: type[T]

    @property
    def secret_name(self):
        return f"{self.environment}/{self.project}"

    async def get_secret(self) -> T:
        value, exp = self.cached_secret
        now = int(time.time())
        if exp < now:
            value, _ = await asyncio.to_thread(
                self.secret_model.load_secret, self.secret_name, self.region,
            )
            self.cached_secret = (value, now + self.cache_ttl)
        return value


def escape_string(value: str | None) -> str | None:
    if not value:
        return None
    return value.replace("\\t", "\t").replace("\\n", "\n")


EscapedSecretStr = Annotated[SecretStr, BeforeValidator(escape_string)]
