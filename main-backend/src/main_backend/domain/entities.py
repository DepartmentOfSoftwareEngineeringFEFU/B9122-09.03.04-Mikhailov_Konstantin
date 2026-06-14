from __future__ import annotations

from dataclasses import dataclass, field

from datetime import datetime

from typing import Any, Optional

from uuid import UUID, uuid4

from ..core.constants import ForecastHorizon, PredictionStatus

@dataclass

class PredictionEntity:

    id: UUID

    user_id: UUID

    features: dict[str, Any]

    predicted_price: float

    predicted_price_per_sqm: float

    horizon: ForecastHorizon

    confidence: float

    model_version: str

    status: PredictionStatus

    comparables: Optional[list[dict]] = None

    error_message: Optional[str] = None

    ip_address: Optional[str] = None

    user_agent: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)

    updated_at: datetime = field(default_factory=datetime.utcnow)

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

        comparables: Optional[list[dict]] = None,

        ip_address: Optional[str] = None,

        user_agent: Optional[str] = None,

    ) -> "PredictionEntity":

        return cls(

            id=uuid4(),

            user_id=user_id,

            features=features,

            predicted_price=predicted_price,

            predicted_price_per_sqm=predicted_price_per_sqm,

            horizon=horizon,

            confidence=confidence,

            model_version=model_version,

            status=PredictionStatus.SUCCESS,

            comparables=comparables,

            ip_address=ip_address,

            user_agent=user_agent,

        )

    @classmethod

    def create_failed(

        cls,

        user_id: UUID,

        features: dict[str, Any],

        horizon: ForecastHorizon,

        error_message: str,

        ip_address: Optional[str] = None,

        user_agent: Optional[str] = None,

    ) -> "PredictionEntity":

        return cls(

            id=uuid4(),

            user_id=user_id,

            features=features,

            predicted_price=0.0,

            predicted_price_per_sqm=0.0,

            horizon=horizon,

            confidence=0.0,

            model_version="unknown",

            status=PredictionStatus.FAILED,

            error_message=error_message,

            ip_address=ip_address,

            user_agent=user_agent,

        )
