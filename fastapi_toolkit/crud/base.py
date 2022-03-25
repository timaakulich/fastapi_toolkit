from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import (
    delete,
    func,
    select,
)

from fastapi_toolkit.db import create_session
from fastapi_toolkit.db.base_class import BaseModel as Model

ModelType = TypeVar('ModelType', bound=Model)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUDBase:
    def __init__(self, model):
        self.model = model

    def get_model_id(self):
        return self.model.id

    @staticmethod
    def _get_filtered_queryset(exp, filter_query):
        for query in filter_query:
            exp = exp.filter(query)
        return exp

    @staticmethod
    def _get_paginated_queryset(exp, offset, limit):
        if limit is not None:
            exp = exp.limit(limit)
        if offset is not None:
            exp = exp.offset(offset)
        return exp

    @staticmethod
    def _get_sorted_queryset(exp, order_by):
        if order_by:
            exp = exp.order_by(*order_by)
        return exp

    async def count(self, filter_query=tuple(), session=None):
        queryset = select(func.count(self.get_model_id()))
        queryset = self._get_filtered_queryset(queryset, filter_query)
        async with create_session(session) as session:
            count = (await session.execute(queryset)).scalar()
        return count

    async def get(
            self,
            condition,
            session=None
    ) -> ModelType:
        async with create_session(session) as session:
            return (await session.execute(
                select(self.model).filter(condition)
            )).scalars().first()

    async def list(
            self,
            offset: int = 0,
            limit: int = 100,
            order_by: tuple = tuple(),
            filter_query: tuple = tuple(),
            estimate_count: bool = True,
            session=None
    ) -> tuple[list[ModelType], int]:

        queryset = select(self.model)
        queryset = self._get_filtered_queryset(queryset, filter_query)
        queryset = self._get_sorted_queryset(queryset, order_by)
        queryset = self._get_paginated_queryset(queryset, offset, limit)

        count = None
        async with create_session(session) as session:
            items = (await session.execute(queryset)).scalars()
            if estimate_count:
                count = await self.count(filter_query, session=session)
        return items, count

    async def create(
            self,
            obj_in: CreateSchemaType = None,
            additional_data: dict = None,
            session=None,
            **data,
    ) -> ModelType:
        if obj_in:
            data = obj_in.dict()
        if additional_data:
            data.update(additional_data)
        item = self.model(
            **data
        )
        async with create_session(session) as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return item

    async def update(
            self,
            db_obj: ModelType,
            obj_in: UpdateSchemaType = None,
            session=None,
            **update_data
    ) -> ModelType:
        if obj_in:
            update_data = obj_in.dict(exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_obj, k, v)
        async with create_session(session) as session:
            await session.merge(db_obj)
            await session.commit()
        return db_obj

    async def delete(self, condition, session=None):
        async with create_session(session) as session:
            await session.execute(
                delete(self.model).filter(condition)
            )
            await session.commit()

    async def get_or_create(self, condition, session=None, **defaults):
        created = False
        async with create_session(session) as session:
            obj = await self.get(condition, session)
            if obj is None:
                obj = await self.create(**defaults)
                created = True
        return obj, created
