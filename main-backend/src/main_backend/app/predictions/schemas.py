from datetime import datetime

from typing import Any, Optional

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ...core.constants import ForecastHorizon, PredictionStatus

class FlatFeaturesSchema(BaseModel):

    model_config = ConfigDict(extra="allow")                              

    total_meters: float = Field(..., gt=0, le=1000)

    living_meters: float = Field(..., ge=0)

    kitchen_meters: float = Field(..., ge=0)

    rooms_count: int = Field(..., ge=0, le=10)

    floor: int = Field(..., ge=1)

    floors_count: int = Field(..., ge=1)

    floor_ratio: float = Field(..., ge=0, le=1)

    living_ratio: float = Field(..., ge=0, le=1)

    kitchen_ratio: float = Field(..., ge=0, le=1)

    building_age: float = Field(..., ge=0)

    year_of_construction: float = Field(..., ge=1850, le=2100)

    latitude: float = Field(..., ge=-90, le=90)

    longitude: float = Field(..., ge=-180, le=180)

    dist_to_center_km: float = Field(..., ge=0)

    dist_to_sea_km: float = Field(..., ge=0)

    infrastructure_count: int = Field(..., ge=0)

    security_score: int = Field(..., ge=0, le=5)

    has_intercom: int = Field(..., ge=0, le=1)

    has_closed_territory: int = Field(..., ge=0, le=1)

    has_code_door: int = Field(..., ge=0, le=1)

    has_garage: int = Field(..., ge=0, le=1)

    has_concierge: int = Field(..., ge=0, le=1)

    offer_photos_count: int = Field(..., ge=0)

    house_photos_count: int = Field(..., ge=0)

    has_plan_photo: int = Field(..., ge=0, le=1)

class PredictionRequestSchema(BaseModel):

    features: FlatFeaturesSchema

    horizon: ForecastHorizon = ForecastHorizon.NOW

class PredictionResponseSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    user_id: UUID

    predicted_price: float

    predicted_price_per_sqm: float

    horizon: ForecastHorizon

    confidence: float

    model_version: str

    status: PredictionStatus               

    error_message: Optional[str] = None               

    comparables: Optional[list[dict[str, Any]]] = None

    created_at: datetime

    @property

    def trend_description(self) -> str:

        return {

            ForecastHorizon.NOW: "Текущая рыночная оценка",

            ForecastHorizon.SIX_MONTHS: "Умеренный рост (+3.2%)",

            ForecastHorizon.ONE_YEAR: "Прогноз на год (+6.8%)",

        }[self.horizon]

class PredictionListItemSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    predicted_price: float

    predicted_price_per_sqm: float

    horizon: ForecastHorizon

    total_meters: float

    rooms_count: int

    created_at: datetime

    @classmethod

    def from_entity(cls, entity) -> "PredictionListItemSchema":

        features = entity.features

        return cls(

            id=entity.id,

            predicted_price=entity.predicted_price,

            predicted_price_per_sqm=entity.predicted_price_per_sqm,

            horizon=entity.horizon,

            total_meters=features.get("total_meters", 0),

            rooms_count=features.get("rooms_count", 0),

            created_at=entity.created_at,

        )

class PredictionHistoryResponseSchema(BaseModel):

    items: list[PredictionListItemSchema]

    total: int

    limit: int

    offset: int
