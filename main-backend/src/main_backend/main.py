import logging

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from .api.responses import ApiResponse

from .app.middleware.exception_handler import register_exception_handlers

from .app.middleware.request_id import RequestIDMiddleware

from .app.predictions.router import router as predictions_router

from .config import settings

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:

    app = FastAPI(

        title=settings.APP_NAME,

        version=settings.APP_VERSION,

        description="Real Estate Forecasting - Main Service",

        docs_url="/docs" if settings.DEBUG else None,

        redoc_url="/redoc" if settings.DEBUG else None,

    )

    app.add_middleware(

        CORSMiddleware,

        allow_origins=settings.CORS_ORIGINS,

        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,

        allow_methods=["*"],

        allow_headers=["*"],

    )

    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)

    app.include_router(predictions_router)

    @app.get("/health", tags=["Health"])

    async def health_check():

        return ApiResponse(data={"status": "ok", "service": "main-backend"})

    logger.info(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} initialized")

    return app

app = create_app()
