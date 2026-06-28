from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_predictor

from .schemas import HealthResponse

from .v1.predictions import router as predictions_router

def create_app() -> FastAPI:

    app = FastAPI(

        title="Forecasting Service",

        version="0.1.0",

        description="Real Estate Price Forecasting API",

    )

    app.add_middleware(

        CORSMiddleware,

        allow_origins=["*"],                            

        allow_credentials=True,

        allow_methods=["*"],

        allow_headers=["*"],

    )

    @app.get("/health", response_model=HealthResponse, tags=["Health"])

    async def health_check():

        try:

            predictor = get_predictor()

            return HealthResponse(

                status="ok",

                service="forecasting-service",

                model_loaded=True,

                model_version=predictor._model_version,

            )

        except Exception as e:

            return HealthResponse(

                status="error",

                service="forecasting-service",

                model_loaded=False,

                model_version="unknown",

            )

    app.include_router(predictions_router)

    return app

app = create_app()
