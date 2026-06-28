"""
Domain entities for forecasting service.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from ..core.constants import ForecastHorizon


@dataclass
class FlatFeatures:
    """Flat features for prediction."""

    # Numeric features
    total_meters: float
    living_meters: float
    kitchen_meters: float
    rooms_count: int
    floor: int
    floors_count: int
    floor_ratio: float
    living_ratio: float
    kitchen_ratio: float
    building_age: float
    year_of_construction: float
    latitude: float
    longitude: float
    dist_to_center_km: float
    dist_to_sea_km: float
    infrastructure_count: int
    security_score: int

    # Boolean features
    has_intercom: int
    has_closed_territory: int
    has_code_door: int
    has_garage: int
    has_concierge: int
    offer_photos_count: int
    house_photos_count: int
    has_plan_photo: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_meters": self.total_meters,
            "living_meters": self.living_meters,
            "kitchen_meters": self.kitchen_meters,
            "rooms_count": self.rooms_count,
            "floor": self.floor,
            "floors_count": self.floors_count,
            "floor_ratio": self.floor_ratio,
            "living_ratio": self.living_ratio,
            "kitchen_ratio": self.kitchen_ratio,
            "building_age": self.building_age,
            "year_of_construction": self.year_of_construction,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "dist_to_center_km": self.dist_to_center_km,
            "dist_to_sea_km": self.dist_to_sea_km,
            "infrastructure_count": self.infrastructure_count,
            "security_score": self.security_score,
            "has_intercom": self.has_intercom,
            "has_closed_territory": self.has_closed_territory,
            "has_code_door": self.has_code_door,
            "has_garage": self.has_garage,
            "has_concierge": self.has_concierge,
            "offer_photos_count": self.offer_photos_count,
            "house_photos_count": self.house_photos_count,
            "has_plan_photo": self.has_plan_photo,
        }


@dataclass
class Prediction:
    """Prediction entity."""

    id: UUID
    user_id: UUID
    features: dict[str, Any]
    predicted_price: float
    predicted_price_per_sqm: float
    horizon: ForecastHorizon
    confidence: float
    model_version: str
    status: str = "success"
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        user_id: UUID,
        features: dict[str, Any],
        predicted_price: float,
        predicted_price_per_sqm: float,
        horizon: ForecastHorizon,
        confidence: float,
        model_version: str,
    ) -> "Prediction":
        """Create prediction entity."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            features=features,
            predicted_price=predicted_price,
            predicted_price_per_sqm=predicted_price_per_sqm,
            horizon=horizon,
            confidence=confidence,
            model_version=model_version,
            status="success",
        )

    @classmethod
    def create_failed(
        cls,
        user_id: UUID,
        features: dict[str, Any],
        horizon: ForecastHorizon,
        error_message: str,
    ) -> "Prediction":
        """Create failed prediction entity."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            features=features,
            predicted_price=0.0,
            predicted_price_per_sqm=0.0,
            horizon=horizon,
            confidence=0.0,
            model_version="unknown",
            status="failed",
            error_message=error_message,
        )


@dataclass
class ModelInfo:
    """Model information."""

    version: str
    algorithm: str
    r2_score: float
    mape: float
    rmse: float
    trained_at: datetime
    is_active: bool
    features_count: int