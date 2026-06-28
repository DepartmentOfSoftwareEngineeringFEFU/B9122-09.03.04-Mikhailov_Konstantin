from __future__ import annotations

from types import TracebackType

from typing import Optional, Protocol, Self, Sequence

from uuid import UUID

class PredictionRepositoryProtocol(Protocol):

    async def create(self, entity: "PredictionEntity") -> "PredictionEntity": ...

    async def get_by_id(self, prediction_id: UUID) -> Optional["PredictionEntity"]: ...

    async def get_by_user(

        self,

        user_id: UUID,

        limit: int = 20,

        offset: int = 0,

    ) -> Sequence["PredictionEntity"]: ...

    async def delete(self, prediction_id: UUID, user_id: UUID) -> bool: ...

    async def count_by_user(self, user_id: UUID) -> int: ...

class UnitOfWorkProtocol(Protocol):

    predictions: PredictionRepositoryProtocol

    async def __aenter__(self) -> Self: ...

    async def __aexit__(

        self,

        exc_type: Optional[type[BaseException]],

        exc_val: Optional[BaseException],

        exc_tb: Optional[TracebackType],

    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

class AuthClientProtocol(Protocol):

    async def get_user(self, user_id: UUID) -> Optional["UserInfo"]: ...

    async def invalidate_cache(self, user_id: UUID) -> None: ...

class ForecastingClientProtocol(Protocol):

    async def predict(self, features: dict, horizon: str) -> "PredictionResult": ...
