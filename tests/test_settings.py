from unittest.mock import patch

import pytest

from fastapi_toolkit.settings import (
    BaseSettings,
    GitSettings,
    SecretSettings,
    escape_string,
)


class TestEscapeString:
    def test_escape_newline(self):
        assert escape_string("hello\\nworld") == "hello\nworld"

    def test_escape_tab(self):
        assert escape_string("hello\\tworld") == "hello\tworld"

    def test_none(self):
        assert escape_string(None) is None

    def test_empty(self):
        assert escape_string("") is None


class TestGitSettings:
    def test_defaults(self):
        gs = GitSettings()
        assert gs.hash is None
        assert gs.branch is None


class TestSecretSettings:
    def test_load_secret_without_botocore(self):
        with patch.dict("sys.modules", {"botocore": None, "botocore.session": None}):
            with pytest.raises(ImportError, match="botocore is required"):
                SecretSettings.load_secret("test/secret", "us-east-1")


class TestBaseSettings:
    def test_secret_name(self):
        class MySecrets(SecretSettings):
            pass

        settings = BaseSettings(
            project="myapp",
            environment="dev",
            region="us-east-1",
            secret_model=MySecrets,
        )
        assert settings.secret_name == "dev/myapp"

    async def test_get_secret_caches(self):
        class MySecrets(SecretSettings):
            api_key: str = "loaded"

        mock_secret = MySecrets()

        class Settings(BaseSettings[MySecrets]):
            pass

        settings = Settings(
            project="myapp",
            environment="dev",
            region="us-east-1",
            secret_model=MySecrets,
        )

        with patch.object(
            MySecrets, "load_secret", return_value=(mock_secret, True),
        ) as mock_load:
            secret1 = await settings.get_secret()
            secret2 = await settings.get_secret()

            assert secret1.api_key == "loaded"
            assert secret1 is secret2
            mock_load.assert_called_once()
