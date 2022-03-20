from fastapi_toolkit.crud.base import CRUDBase
from fastapi_toolkit.db import create_session
from tests.models import Book


class TestCRUDGet:
    async def _create_book(self, **kwargs):
        async with create_session() as session:
            session.add(Book(**kwargs))
            await session.commit()

    async def test_one_ok(self, db):
        test_name = 'test_name'

        await self._create_book(name=test_name)

        book = await CRUDBase(Book).get(Book.name == test_name)
        assert book.name == test_name

    async def test_no_one_ok(self, db):
        await self._create_book(name='test_name')

        book = await CRUDBase(Book).get(Book.name == 'wrong_name')
        assert book is None
