from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class DecodedUserModel(BaseModel):
    id: UUID = Field(..., alias="sub")
    permissions: dict[str, int] = Field(default_factory=dict)
    version: int = 0
    jid: UUID | None = None
