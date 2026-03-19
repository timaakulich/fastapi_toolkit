import enum
from typing import Any


class Error(enum.StrEnum):
    auth_error = 'auth_error'
    request_validation_error = 'request_validation_error'
    jwt_validation_error = 'jwt_validation_error'
    permissions_error = 'permissions_error'
    object_not_found = 'object_not_found'
    integrity_error = 'integrity_error'


def exc_detail(code: enum.StrEnum, error: str | None = None, info: Any | None = None) -> dict[str, Any]:
    return {
        'code': code.value,
        'error': error,
        'info': info
    }
