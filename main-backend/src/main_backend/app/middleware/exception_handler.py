import logging

from typing import Any

from fastapi import FastAPI, Request, status

from fastapi.responses import JSONResponse

from ...api.responses import ErrorDetail, ErrorResponse

from ...core.exceptions import (

    AuthServiceUnavailable,

    ForecastingServiceUnavailable,

    InvalidFeaturesError,

    MainBackendError,

    PredictionNotFoundError,

    UserDisabledError,

    UserNotFoundError,

)

logger = logging.getLogger(__name__)

def _make_response(code: str, message: str, http_status: int) -> JSONResponse:

    return JSONResponse(

        status_code=http_status,

        content=ErrorResponse(

            error=ErrorDetail(code=code, message=message)

        ).model_dump(mode="json"),

    )

def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(PredictionNotFoundError)

    async def prediction_not_found(request: Request, exc: PredictionNotFoundError):

        return _make_response(exc.code, exc.message, status.HTTP_404_NOT_FOUND)

    @app.exception_handler(UserNotFoundError)

    async def user_not_found(request: Request, exc: UserNotFoundError):

        return _make_response(exc.code, exc.message, status.HTTP_404_NOT_FOUND)

    @app.exception_handler(UserDisabledError)

    async def user_disabled(request: Request, exc: UserDisabledError):

        return _make_response(exc.code, exc.message, status.HTTP_403_FORBIDDEN)

    @app.exception_handler(InvalidFeaturesError)

    async def invalid_features(request: Request, exc: InvalidFeaturesError):

        return _make_response(exc.code, exc.message, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(ForecastingServiceUnavailable)

    async def forecasting_unavailable(

        request: Request, exc: ForecastingServiceUnavailable

    ):

        logger.error(f"Forecasting service unavailable: {exc.message}")

        return _make_response(

            exc.code, exc.message, status.HTTP_503_SERVICE_UNAVAILABLE

        )

    @app.exception_handler(AuthServiceUnavailable)

    async def auth_unavailable(request: Request, exc: AuthServiceUnavailable):

        logger.error(f"Auth service unavailable: {exc.message}")

        return _make_response(

            exc.code, exc.message, status.HTTP_503_SERVICE_UNAVAILABLE

        )

    @app.exception_handler(MainBackendError)

    async def main_backend_error(request: Request, exc: MainBackendError):

        logger.error(f"Main backend error: {exc.message}", exc_info=True)

        return _make_response(

            exc.code, exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR

        )

    @app.exception_handler(Exception)

    async def unhandled_exception(request: Request, exc: Exception):

        logger.exception(f"Unhandled exception: {exc}")

        return _make_response(

            "INTERNAL_ERROR",

            "Unexpected error occurred",

            status.HTTP_500_INTERNAL_SERVER_ERROR,

        )
