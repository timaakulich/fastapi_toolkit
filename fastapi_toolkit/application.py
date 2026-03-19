from fastapi import (
    FastAPI,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from fastapi_toolkit.exceptions import Error, exc_detail


def prepare_app(app: FastAPI) -> FastAPI:

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse({
            'detail': exc_detail(
                code=Error.request_validation_error,
                error='Invalid request',
                info=jsonable_encoder(exc.errors())
            )
        }, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    return app
