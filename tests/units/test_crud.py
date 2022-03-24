from fastapi_toolkit.crud.base import CRUDBase
from tests.models import Book
from tests.schemas import BookSchema


class TestCRUDGet:
    async def test_one_ok(self, mixer):
        test_book = await mixer.blend(Book)
        book = await CRUDBase(Book).get(Book.title == test_book.title)
        assert BookSchema.from_orm(book) == BookSchema.from_orm(test_book)

    async def test_no_one_ok(self, mixer):
        await mixer.blend(Book, title='some_title')
        book = await CRUDBase(Book).get(Book.title == 'wrong_title')
        assert book is None


class TestCRUDCount:
    async def test_count_ok(self, mixer):
        test_count = 3
        await mixer.cycle(test_count).blend(Book)
        count = await CRUDBase(Book).count()
        assert count == test_count

    async def test_count_with_filter_ok(self, mixer):
        test_count = 3
        await mixer.cycle(test_count).blend(
            Book,
            title=mixer.sequence('Title_{0}'),
            page_amount=mixer.sequence()
        )
        count = await CRUDBase(Book).count((Book.title == 'Title_1', ))
        assert count == 1
