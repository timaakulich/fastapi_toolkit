from typing import List

from pydantic import create_model


def pagination_model(model, prefix=''):
    return create_model(
        f'{prefix}Pagination{model.__name__}',
        meta=(dict, ...),
        result=(List[model], ...)
    )
