from typing import Any

from pydantic import BaseModel


class DetailModel(BaseModel):
    code: str
    error: str | None = None
    info: Any | None = None


class ErrorResponseModel(BaseModel):
    detail: DetailModel
