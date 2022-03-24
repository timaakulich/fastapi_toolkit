from pydantic import BaseModel


class BookSchema(BaseModel):
    id: int
    title: str
    page_amount: int

    class Config:
        orm_mode = True
