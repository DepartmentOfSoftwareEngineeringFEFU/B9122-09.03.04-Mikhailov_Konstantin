from __future__ import annotations

import logging

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ...ml.predictor import FlatFeatures, PredictionResult, PricePredictor

from ..dependencies import get_predictor

from ..schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])

@router.post("/", response_model=PredictionResponse)

async def predict_price(

    request: PredictionRequest,

    predictor: Annotated[PricePredictor, Depends(get_predictor)],

):

    try:

        features = FlatFeatures(**request.features)

        result: PredictionResult = predictor.predict(features)

        multiplier = 1.0

        if request.horizon == "6_months":

            multiplier = 1.032         

        elif request.horizon == "1_year":

            multiplier = 1.068         

        predicted_price = result.predicted_price * multiplier

        predicted_price_per_sqm = result.predicted_price_per_sqm * multiplier

        logger.info(

            f"Prediction completed: "

            f"price={predicted_price:.0f}, "

            f"horizon={request.horizon}, "

            f"multiplier={multiplier}"

        )

        return PredictionResponse(

            status="ok",

            predicted_price=predicted_price,

            predicted_price_per_sqm=predicted_price_per_sqm,

            confidence=result.confidence,

            model_version=result.model_version,

            horizon=request.horizon,

        )

    except Exception as e:

        logger.error(f"Prediction failed: {e}", exc_info=True)

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=f"Prediction failed: {str(e)}",

        )
