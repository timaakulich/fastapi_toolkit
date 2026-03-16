# Standard Library
import builtins
from functools import reduce

# Third Party Library
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from fastapi_toolkit.db import async_session


class BaseCRUD:
    database = "default"

    def __init__(self, model) -> None:
        self.model = model

    def get_model_id(self):
        return self.model.id

    async def list(
        self,
        condition=None,
        joins: list[tuple] | None = None,
        order_by: tuple | None = None,
        limit: int | None = None,
        offset: int | None = None,
        fields: tuple | None = None,
        for_update: bool = False,
        for_update_kwargs: dict | None = None,
        unique: bool = True,
        session=None,
    ):
        query = select(*fields) if fields else select(self.model)
        if for_update:
            query = query.with_for_update(**for_update_kwargs)
        if joins:
            query = reduce(lambda x, y: x.join(*y), joins, query)
        if condition is not None:
            query = query.where(condition)
        if order_by:
            query = query.order_by(*order_by)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        async with async_session(session, database=self.database) as session:
            result = await session.execute(query)
            if not fields:
                result = result.scalars()
            if unique:
                result = result.unique()
            return result

    async def count(
        self,
        condition=None,
        joins: builtins.list[tuple] | None = None,
        session=None,
    ) -> int:
        query = select(func.count(self.get_model_id()))
        if joins:
            query = reduce(lambda x, y: x.join(*y), joins, query)
        if condition is not None:
            query = query.where(condition)
        async with async_session(session, database=self.database) as session:
            count = (await session.execute(query)).scalar()
        return count

    async def get(
        self,
        condition,
        joins: builtins.list[tuple] | None = None,
        for_update: bool = False,
        for_update_kwargs: dict | None = None,
        session=None,
    ):
        return (
            await self.list(
                condition,
                joins,
                session=session,
                for_update=for_update,
                for_update_kwargs=for_update_kwargs,
            )
        ).first()

    async def create(
        self,
        session=None,
        commit=True,
        **kwargs,
    ):
        async with async_session(session, database=self.database) as session:
            obj = self.model(**kwargs)
            session.add(obj)
            await session.flush()
            await session.refresh(obj)
            if commit:
                await session.commit()
            return obj

    async def bulk_create(self, items: builtins.list[dict], session=None, commit=True):
        items = [self.model(**item) for item in items]
        async with async_session(session, database=self.database) as session:
            session.add_all(items)
            if commit:
                await session.commit()

    async def update(
        self,
        condition,
        session=None,
        commit=True,
        **kwargs,
    ):
        async with async_session(session, database=self.database) as session:
            query = update(self.model).where(condition).values(**kwargs)
            result = await session.execute(query)
            if commit:
                await session.commit()
            return result

    async def delete(
        self,
        condition=None,
        session=None,
        commit=True,
    ):
        async with async_session(session, database=self.database) as session:
            query = delete(self.model)
            if condition is not None:
                query = query.where(condition)
            await session.execute(query)
            if commit:
                await session.commit()

    async def get_or_create(
        self,
        condition,
        session=None,
        commit=True,
        **defaults,
    ):
        created = False
        async with async_session(session, database=self.database) as session:
            obj = await self.get(condition, session)
            if obj is None:
                orm_stmt = (
                    select(self.model)
                    .from_statement(
                        insert(self.model)
                        .values(
                            **defaults,
                        )
                        .on_conflict_do_nothing()
                        .returning(self.model),
                    )
                    .execution_options(populate_existing=True)
                )
                obj = (await session.execute(orm_stmt)).scalar()
                if commit:
                    await session.commit()
                # sometimes previous statement doesn't return inserted object
                if not obj:
                    obj = await self.get(condition, session)
                created = True
        return obj, created
