from collections.abc import Awaitable, Callable
from inspect import iscoroutinefunction
from typing import TypeVar

import jwt
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    SecurityScopes,
)
from jwt import PyJWTError

from fastapi_toolkit.exceptions import Error, exc_detail
from fastapi_toolkit.schemas.user import DecodedUserModel
from fastapi_toolkit.security import HTTPBearer

T = TypeVar('T', bound=DecodedUserModel)


def get_user_dependency(
        jwt_secret_dependency: Callable[..., str | Awaitable[str]],
        alg_dependency: Callable[..., str | Awaitable[str]],
        project_dependency: Callable[..., str | Awaitable[str]],
        user_model: type[T],
        token_validator: Callable[[T], None | Awaitable[None]] | None = None,
) -> Callable[..., Awaitable[T]]:
    async def get_user(
            security_scopes: SecurityScopes,
            auth: HTTPAuthorizationCredentials = Depends(HTTPBearer(
                auto_error=True
            )),
            jwt_secret: str = Depends(jwt_secret_dependency),
            alg: str = Depends(alg_dependency),
            project: str = Depends(project_dependency),
    ) -> T:
        try:
            decoded_token = jwt.decode(auth.credentials, jwt_secret, algorithms=[alg])
        except PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=exc_detail(
                    code=Error.jwt_validation_error,
                    error=str(exc)
                )
            ) from exc
        else:
            decoded_token = user_model.model_validate(decoded_token)

            if token_validator is not None:
                if iscoroutinefunction(token_validator):
                    await token_validator(decoded_token)
                else:
                    token_validator(decoded_token)

            user_permissions = decoded_token.permissions.get(project, 0)
            for scope in (security_scopes.scopes or []):
                scope = int(scope)
                if not (user_permissions & scope == scope):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=exc_detail(
                            code=Error.permissions_error,
                            error='Permissions required',
                            info={
                                'project': project,
                                'required_permission': scope,
                                'user_permissions': user_permissions
                            }
                        )
                    )
            return decoded_token
    return get_user
