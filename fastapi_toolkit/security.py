# Standard Library
import enum

# Third Party Library
from fastapi import (
    HTTPException,
    Request,
    status,
)
from fastapi.security.http import (
    HTTPAuthorizationCredentials,
)
from fastapi.security.http import (
    HTTPBearer as BaseHTTPBearer,
)
from fastapi.security.utils import get_authorization_scheme_param

from fastapi_toolkit.exceptions import Error, exc_detail
from fastapi_toolkit.schemas.response import DetailModel


def get_scopes(*scopes: enum.IntEnum | enum.Flag) -> list[str]:
    return [str(scope.value) for scope in scopes]


class HTTPBearer(BaseHTTPBearer):
    async def __call__(
        self, request: Request
    ) -> HTTPAuthorizationCredentials | None:
        authorization = request.headers.get('Authorization')
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=exc_detail(
                        code=Error.auth_error,
                        error='Not authenticated'
                    )
                )
            else:
                return None
        if scheme.lower() != 'bearer':
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=exc_detail(
                        code=Error.auth_error,
                        error='Invalid authentication credentials'
                    ),
                )
            else:
                return None
        return HTTPAuthorizationCredentials(
            scheme=scheme,
            credentials=credentials
        )


ERROR_AUTH_RESPONSES = {
    status.HTTP_403_FORBIDDEN: {
        'model': DetailModel,
        'description': 'Not authenticated / Invalid authentication credentials',
    }
}
