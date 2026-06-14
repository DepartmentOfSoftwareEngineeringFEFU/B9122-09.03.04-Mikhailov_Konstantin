from __future__ import annotations

from typing import Annotated, AsyncIterator

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.protocols import UnitOfWorkProtocol

from ..external.database.config import async_session_factory

from ..external.database.unit_of_work import UnitOfWork

from ..external.integrations.auth_client import AuthClient

from ..external.integrations.forecasting_client import ForecastingClient

async def get_session() -> AsyncIterator[AsyncSession]:

    async with async_session_factory() as session:

        yield session

async def get_uow() -> AsyncIterator[UnitOfWorkProtocol]:

    uow = UnitOfWork()

    async with uow:

        yield uow

def get_auth_client() -> AuthClient:

    return AuthClient()

def get_forecasting_client() -> ForecastingClient:

    return ForecastingClient()

UoWDep = Annotated[UnitOfWorkProtocol, Depends(get_uow)]

AuthClientDep = Annotated[AuthClient, Depends(get_auth_client)]

ForecastingClientDep = Annotated[ForecastingClient, Depends(get_forecasting_client)]
