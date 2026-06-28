from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):

    features: dict = Field(

        ...,

        description="Признаки квартиры (см. FlatFeatures)",

    )

    horizon: str = Field(

        default="now",

        pattern="^(now|6_months|1_year)$",

        description="Горизонт прогноза",

    )

class PredictionResponse(BaseModel):

    status: str = "ok"

    predicted_price: float

    predicted_price_per_sqm: float

    confidence: float

    model_version: str

    horizon: str

class HealthResponse(BaseModel):

    status: str = "ok"

    service: str = "forecasting-service"

    model_loaded: bool

    model_version: str
