from __future__ import annotations

import logging

from types import TracebackType

from typing import Optional, Self

from sqlalchemy.ext.asyncio import AsyncSession

from ...core.protocols import UnitOfWorkProtocol

from .config import async_session_factory

from .repositories import PredictionRepository

logger = logging.getLogger(__name__)

class UnitOfWork:

    def __init__(self):

        self._session: Optional[AsyncSession] = None

        self.predictions: PredictionRepository

    async def __aenter__(self) -> Self:

        self._session = async_session_factory()

        self.predictions = PredictionRepository(self._session)

        return self

    async def __aexit__(

        self,

        exc_type: Optional[type[BaseException]],

        exc_val: Optional[BaseException],

        exc_tb: Optional[TracebackType],

    ) -> None:

        if self._session is None:

            return

        if exc_type is not None:

            await self.rollback()

            logger.warning(f"Transaction rolled back due to: {exc_val}")

        else:

            await self.commit()

        await self._session.close()

    async def commit(self) -> None:

        if self._session is None:

            return

        await self._session.commit()

    async def rollback(self) -> None:

        if self._session is None:

            return

        await self._session.rollback()
