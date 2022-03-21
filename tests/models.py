from sqlalchemy import (
    Column,
    Integer,
    String,
)

from fastapi_toolkit.db import BaseModel

__all__ = (
    'Book',
)


class Book(BaseModel):
    id = Column(Integer, primary_key=True)
    name = Column(String(length=42))
