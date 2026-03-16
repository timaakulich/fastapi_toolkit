# fastapi-toolkit

[![PyPI version](https://badge.fury.io/py/fastapi-toolkit.svg)](https://badge.fury.io/py/fastapi-toolkit)
[![Python](https://img.shields.io/pypi/pyversions/fastapi-toolkit.svg)](https://pypi.org/project/fastapi-toolkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Common toolkit for **FastAPI** + **SQLAlchemy 2.0** projects: async DB sessions, base CRUD, settings with AWS Secrets Manager.

## Features

- **Async database sessions** — multi-database support with context-managed sessions
- **Base CRUD** — generic async CRUD operations (list, get, create, update, delete, get_or_create)
- **Declarative base model** — SQLAlchemy declarative base with automatic table naming
- **Settings management** — pydantic-settings with cached AWS Secrets Manager integration
- **Type-safe** — full type hints with `py.typed` marker

## Installation

```bash
pip install fastapi-toolkit
```

With AWS Secrets Manager support:

```bash
pip install fastapi-toolkit[aws]
```

## Quick Start

### Database Setup

```python
from fastapi_toolkit import init_db, async_session

# Initialize on app startup
init_db("postgresql+asyncpg://user:pass@localhost/mydb")

# Use sessions
async with async_session() as session:
    result = await session.execute(...)
```

### Models

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from fastapi_toolkit import BaseModel


class User(BaseModel):
    __table_name__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200))
```

### CRUD

```python
from fastapi_toolkit import BaseCRUD

user_crud = BaseCRUD(User)

# List
users = await user_crud.list()

# Get by condition
user = await user_crud.get(User.id == 1)

# Create
user = await user_crud.create(name="Alice", email="alice@example.com")

# Update
await user_crud.update(User.id == 1, name="Bob")

# Delete
await user_crud.delete(User.id == 1)

# Get or create
user, created = await user_crud.get_or_create(
    User.email == "alice@example.com",
    name="Alice",
    email="alice@example.com",
)
```

### Settings with AWS Secrets Manager

```python
from fastapi_toolkit import BaseSettings, SecretSettings, EscapedSecretStr


class MySecrets(SecretSettings):
    db_password: EscapedSecretStr = None
    api_key: str = ""


class Settings(BaseSettings[MySecrets]):
    project: str = "myapp"
    environment: str = "dev"
    region: str = "us-east-1"
    secret_model: type = MySecrets


settings = Settings()

# Secrets are loaded from AWS Secrets Manager, cached with TTL
secrets = await settings.get_secret()
```

### Multi-Database Support

```python
from fastapi_toolkit import init_db, BaseCRUD

# Initialize multiple databases
init_db("postgresql+asyncpg://localhost/primary", database="default")
init_db("postgresql+asyncpg://localhost/analytics", database="analytics")


# Use specific database in CRUD
class AnalyticsCRUD(BaseCRUD):
    database = "analytics"

analytics_crud = AnalyticsCRUD(Event)
```

## API Reference

### `init_db(database_dsn, database="default", engine_kwargs=None, session_maker_kwargs=None)`

Initialize an async database engine and session factory.

### `async_session(exists_session=None, database="default")`

Async context manager for database sessions. Reuses existing session if provided.

### `BaseCRUD(model)`

Generic async CRUD class with methods:

| Method | Description |
|--------|-------------|
| `list(condition, joins, order_by, limit, offset, fields, unique, session)` | List records with filtering and pagination |
| `count(condition, joins, session)` | Count matching records |
| `get(condition, joins, session)` | Get single record |
| `create(session, commit, **kwargs)` | Create a record |
| `bulk_create(items, session, commit)` | Bulk create records |
| `update(condition, session, commit, **kwargs)` | Update matching records |
| `delete(condition, session, commit)` | Delete matching records |
| `get_or_create(condition, session, commit, **defaults)` | Get existing or create new |

### `BaseSettings[T]`

Pydantic settings with cached AWS Secrets Manager:

| Property / Method | Description |
|-------------------|-------------|
| `secret_name` | Auto-generated secret name: `{environment}/{project}` |
| `await get_secret()` | Load and cache secret (non-blocking) |

## Development

```bash
# Clone the repository
git clone https://github.com/timaakulich/fastapi-toolkit.git
cd fastapi-toolkit

# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check .

# Run type checker
mypy fastapi_toolkit
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
