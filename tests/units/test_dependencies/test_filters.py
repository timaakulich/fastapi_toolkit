from dataclasses import dataclass
from typing import Any
from unittest.mock import patch

import pytest

from fastapi_toolkit.dependencies import filter_by_fields
from fastapi_toolkit.filters import filter_
from fastapi_toolkit.filters.func import (
    contained_by,
    contains,
    eq,
    gt,
    in_,
    is_null,
    lte,
)
from tests.models import Book


@dataclass
class QueryMock:
    default: Any
    alias: str


@patch('fastapi_toolkit.dependencies.filter.Query', QueryMock)
class TestFilters:
    @pytest.mark.parametrize(
        ('test_fields', 'result_fields'),
        (
            (
                {
                    'title': filter_(Book.title, (eq,)),
                    'page_amount': filter_(Book.page_amount, (gt, lte), str),
                },
                {
                    'title__eq': QueryMock(None, alias='title__eq'),
                    'page_amount__gt': QueryMock(
                        None, alias='page_amount__gt'
                    ),
                    'page_amount__lte': QueryMock(
                        None, alias='page_amount__lte'
                    )
                }
            ),
            (
                {
                    'title': filter_(Book.title, (in_, contains)),
                    'page_amount': filter_(
                        Book.page_amount, (is_null, contained_by), str
                    ),
                },
                {
                    'title__in': QueryMock(None, alias='title__in[]'),
                    'title__contains': QueryMock(
                        None, alias='title__contains[]'
                    ),
                    'page_amount__is_null': QueryMock(
                        None, alias='page_amount__is_null'
                    ),
                    'page_amount__contained_by': QueryMock(
                        None, alias='page_amount__contained_by[]'
                    )
                }
            ),
        )
    )
    def test_result_dataclass__ok(
            self, test_fields: dict, result_fields: dict
    ):
        result = filter_by_fields(test_fields)
        assert result.__name__ == 'FilterQueryParams'
        for field_name in result.__dataclass_fields__:
            assert getattr(result, field_name) == result_fields[field_name]
