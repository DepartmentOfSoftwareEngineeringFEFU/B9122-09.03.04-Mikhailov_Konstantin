from __future__ import annotations

import logging

from typing import Sequence

from uuid import UUID

from ...core.constants import MARKET_TRENDS, ForecastHorizon, PredictionStatus

from ...core.exceptions import (

    PredictionNotFoundError,

    UserDisabledError,

    UserNotFoundError,

)

from ...core.protocols import UnitOfWorkProtocol

from ...domain.entities import PredictionEntity

from ...external.integrations.auth_client import AuthClient

from ...external.integrations.forecasting_client import ForecastingClient

logger = logging.getLogger(__name__)

class PredictionService:

    def __init__(

        self,

        uow: UnitOfWorkProtocol,

        auth_client: AuthClient,

        forecasting_client: ForecastingClient,

    ):

        self._uow = uow

        self._auth_client = auth_client

        self._forecasting_client = forecasting_client

    async def create_prediction(

        self,

        user_id: UUID,

        features: dict,

        horizon: ForecastHorizon,

        ip_address: str | None = None,

        user_agent: str | None = None,

    ) -> PredictionEntity:

        await self._verify_user(user_id)

        try:

            base_result = await self._forecasting_client.predict(

                features=features,

                horizon="now",

            )

        except Exception as e:

            logger.error(f"Forecasting failed: {e}", exc_info=True)

            failed_entity = PredictionEntity.create_failed(

                user_id=user_id,

                features=features,

                horizon=horizon,

                error_message=str(e),

                ip_address=ip_address,

                user_agent=user_agent,

            )

            return await self._uow.predictions.create(failed_entity)

        trend = MARKET_TRENDS[horizon]

        predicted_price = base_result.predicted_price * trend["multiplier"]

        predicted_price_per_sqm = (

            base_result.predicted_price_per_sqm * trend["multiplier"]

        )

        confidence = max(0.0, base_result.confidence + trend["confidence_delta"])

        entity = PredictionEntity.create(

            user_id=user_id,

            features=features,

            predicted_price=predicted_price,

            predicted_price_per_sqm=predicted_price_per_sqm,

            horizon=horizon,

            confidence=confidence,

            model_version=base_result.model_version,

            ip_address=ip_address,

            user_agent=user_agent,

        )

        return await self._uow.predictions.create(entity)

    async def get_prediction(

        self,

        prediction_id: UUID,

        user_id: UUID,

    ) -> PredictionEntity:

        entity = await self._uow.predictions.get_by_id(prediction_id)

        if entity is None or entity.user_id != user_id:

            raise PredictionNotFoundError(str(prediction_id))

        return entity

    async def get_user_predictions(

        self,

        user_id: UUID,

        limit: int = 20,

        offset: int = 0,

    ) -> tuple[Sequence[PredictionEntity], int]:

        predictions = await self._uow.predictions.get_by_user(

            user_id=user_id, limit=limit, offset=offset

        )

        total = await self._uow.predictions.count_by_user(user_id)

        return predictions, total

    async def delete_prediction(

        self,

        prediction_id: UUID,

        user_id: UUID,

    ) -> None:

        deleted = await self._uow.predictions.delete(prediction_id, user_id)

        if not deleted:

            raise PredictionNotFoundError(str(prediction_id))

    async def _verify_user(self, user_id: UUID) -> None:

        user_info = await self._auth_client.get_user(user_id)

        if user_info is None:

            raise UserNotFoundError(str(user_id))

        if not user_info.is_active:

            raise UserDisabledError()
