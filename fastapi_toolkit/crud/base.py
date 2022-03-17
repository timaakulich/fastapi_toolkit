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

    def _get_filtered_queryset(self, exp, filter_query):
        for query in filter_query:
            exp = exp.filter(query)
        return exp

    async def count(self, filter_query=tuple()):
        queryset = select(func.count(self.model.id))
        queryset = self._get_filtered_queryset(queryset, filter_query)
        async with create_session() as session:
            count = (await session.execute(queryset)).scalar()
        return count

    async def get(
            self,
            condition
    ) -> ModelType:
        async with create_session() as session:
            return (await session.execute(
                select(self.model).filter(condition)
            )).scalars().first()

    async def list(
        self,
        offset=0,
        limit=100,
        order_by=tuple(),
        filter_query=tuple(),
    ) -> tuple[list[ModelType], int]:
        queryset = select(self.model)
        queryset = self._get_filtered_queryset(queryset, filter_query)
        if order_by:
            queryset = queryset.order_by(*order_by)
        if limit is not None:
            queryset = queryset.limit(limit)
        if offset is not None:
            queryset = queryset.offset(offset)

        async with create_session() as session:
            items = (await session.execute(queryset)).scalars()
        count = await self.count(filter_query)
        return items, count

    async def create(
            self,
            obj_in: CreateSchemaType = None,
            additional_data: dict = None,
            **data
    ) -> ModelType:
        if obj_in:
            data = obj_in.dict()
        if additional_data:
            data.update(additional_data)
        item = self.model(
            **data
        )
        async with create_session() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
        return item

    async def update(
            self,
            db_obj: ModelType,
            obj_in: UpdateSchemaType = None,
            **update_data
    ) -> ModelType:
        if obj_in:
            update_data = obj_in.dict(skip_defaults=True, exclude_unset=True)
        for k, v in update_data.items():
            setattr(db_obj, k, v)
        async with create_session() as session:
            await session.merge(db_obj)
            await session.commit()
        return db_obj

    async def delete(self, condition):
        async with create_session() as session:
            await session.execute(
                delete(self.model).filter(condition)
            )
            await session.commit()