from __future__ import annotations

import logging

from typing import Optional, Sequence

from uuid import UUID

from sqlalchemy import delete, func, select

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.exceptions import PredictionNotFoundError

from ...domain.entities import PredictionEntity

from .models import PredictionModel

logger = logging.getLogger(__name__)

class PredictionRepository:

    def __init__(self, session: AsyncSession):

        self._session = session

    @staticmethod

    def _to_entity(model: PredictionModel) -> PredictionEntity:

        from ...core.constants import ForecastHorizon, PredictionStatus

        return PredictionEntity(

            id=model.id,

            user_id=model.user_id,

            features=model.features,

            predicted_price=model.predicted_price,

            predicted_price_per_sqm=model.predicted_price_per_sqm,

            horizon=ForecastHorizon(model.horizon),

            confidence=model.confidence,

            model_version=model.model_version,

            status=PredictionStatus(model.status),

            comparables=model.comparables,

            error_message=model.error_message,

            ip_address=model.ip_address,

            user_agent=model.user_agent,

            created_at=model.created_at,

            updated_at=model.updated_at,

        )

    @staticmethod

    def _to_model(entity: PredictionEntity) -> PredictionModel:

        return PredictionModel(

            id=entity.id,

            user_id=entity.user_id,

            features=entity.features,

            predicted_price=entity.predicted_price,

            predicted_price_per_sqm=entity.predicted_price_per_sqm,

            horizon=entity.horizon.value,

            confidence=entity.confidence,

            model_version=entity.model_version,

            status=entity.status.value,

            comparables=entity.comparables,

            error_message=entity.error_message,

            ip_address=entity.ip_address,

            user_agent=entity.user_agent,

            created_at=entity.created_at,

            updated_at=entity.updated_at,

        )

    async def create(self, entity: PredictionEntity) -> PredictionEntity:

        model = self._to_model(entity)

        self._session.add(model)

        await self._session.flush()

        await self._session.refresh(model)

        logger.info(f"Created prediction {model.id} for user {model.user_id}")

        return self._to_entity(model)

    async def get_by_id(self, prediction_id: UUID) -> Optional[PredictionEntity]:

        stmt = select(PredictionModel).where(PredictionModel.id == prediction_id)

        result = await self._session.execute(stmt)

        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def get_by_user(

        self,

        user_id: UUID,

        limit: int = 20,

        offset: int = 0,

    ) -> Sequence[PredictionEntity]:

        stmt = (

            select(PredictionModel)

            .where(PredictionModel.user_id == user_id)

            .order_by(PredictionModel.created_at.desc())

            .limit(limit)

            .offset(offset)

        )

        result = await self._session.execute(stmt)

        models = result.scalars().all()

        return [self._to_entity(m) for m in models]

    async def delete(self, prediction_id: UUID, user_id: UUID) -> bool:

        stmt = delete(PredictionModel).where(

            PredictionModel.id == prediction_id,

            PredictionModel.user_id == user_id,

        )

        result = await self._session.execute(stmt)

        deleted = result.rowcount > 0

        if deleted:

            logger.info(f"Deleted prediction {prediction_id} by user {user_id}")

        return deleted

    async def count_by_user(self, user_id: UUID) -> int:

        stmt = (

            select(func.count())

            .select_from(PredictionModel)

            .where(PredictionModel.user_id == user_id)

        )

        result = await self._session.execute(stmt)

        return result.scalar_one()
