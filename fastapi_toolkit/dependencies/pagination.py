from fastapi import Query

__all__ = (
    'BasePagination',
    'PageNumberPagination',
    'LimitOffsetPagination',
)


class BasePagination:
    @property
    def db_params(self) -> dict:
        raise NotImplementedError

    @property
    def params(self) -> dict:
        raise NotImplementedError

    def _get_positive_or_default(self, value, default=None):
        if value > 0:
            return value
        return default


class PageNumberPagination(BasePagination):
    def __init__(self, page: int = Query(1), page_size: int = Query(10)):
        self.page = page
        self.page_size = page_size

    @property
    def db_params(self) -> dict:
        return {
            'offset': self._get_positive_or_default((self.page - 1) * self.page_size, 0),  # noqa
            'limit': self._get_positive_or_default(self.page_size)
        }

    @property
    def params(self) -> dict:
        return {
            'page': self.page,
            'page_size': self.page_size
        }


class LimitOffsetPagination(BasePagination):
    def __init__(self, offset: int = Query(0), limit: int = Query(10)):
        self.offset = offset
        self.limit = limit

    @property
    def db_params(self):
        return {
            'offset': self._get_positive_or_default(self.offset, 0),
            'limit': self._get_positive_or_default(self.limit)
        }

    @property
    def params(self):
        return self.db_params
