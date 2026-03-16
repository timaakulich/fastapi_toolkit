import pytest

from fastapi_toolkit.crud import BaseCRUD

from .conftest import User


class TestBaseCRUD:
    @pytest.fixture(autouse=True)
    def setup_crud(self):
        self.crud = BaseCRUD(User)

    async def test_list_all(self):
        result = await self.crud.list()
        users = result.all()
        assert len(users) == 3

    async def test_list_with_condition(self):
        result = await self.crud.list(User.name == "Alice")
        users = result.all()
        assert len(users) == 1
        assert users[0].name == "Alice"

    async def test_list_with_limit_offset(self):
        result = await self.crud.list(order_by=(User.id,), limit=2)
        users = result.all()
        assert len(users) == 2

        result = await self.crud.list(order_by=(User.id,), limit=2, offset=1)
        users = result.all()
        assert len(users) == 2
        assert users[0].name == "Bob"

    async def test_list_with_order_by(self):
        result = await self.crud.list(order_by=(User.name.desc(),))
        users = result.all()
        assert users[0].name == "Charlie"
        assert users[-1].name == "Alice"

    async def test_count(self):
        count = await self.crud.count()
        assert count == 3

    async def test_count_with_condition(self):
        count = await self.crud.count(User.name == "Alice")
        assert count == 1

    async def test_get(self):
        user = await self.crud.get(User.id == 1)
        assert user is not None
        assert user.name == "Alice"

    async def test_get_not_found(self):
        user = await self.crud.get(User.id == 999)
        assert user is None

    async def test_create(self):
        user = await self.crud.create(id=10, name="Diana", email="diana@example.com")
        assert user.id == 10
        assert user.name == "Diana"

        fetched = await self.crud.get(User.id == 10)
        assert fetched is not None

    async def test_update(self):
        await self.crud.update(User.id == 1, name="Alice Updated")
        user = await self.crud.get(User.id == 1)
        assert user.name == "Alice Updated"

    async def test_delete(self):
        await self.crud.delete(User.id == 3)
        user = await self.crud.get(User.id == 3)
        assert user is None

    async def test_bulk_create(self):
        items = [
            {"id": 20, "name": "Eve", "email": "eve@example.com"},
            {"id": 21, "name": "Frank", "email": "frank@example.com"},
        ]
        await self.crud.bulk_create(items)
        count = await self.crud.count()
        assert count >= 5


class TestBaseCRUDWithSession:
    @pytest.fixture(autouse=True)
    def setup_crud(self, async_session_factory):
        self.crud = BaseCRUD(User)
        self.session_factory = async_session_factory

    async def test_create_with_existing_session(self):
        async with self.session_factory() as session:
            user = await self.crud.create(
                session=session, commit=False,
                id=30, name="Grace", email="grace@example.com",
            )
            assert user.name == "Grace"
            await session.commit()

        fetched = await self.crud.get(User.id == 30)
        assert fetched is not None
