from __future__ import annotations

import logging

from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from fastapi import status as http_status

from fastapi.responses import JSONResponse

from ...core.constants import PredictionStatus

from ...api.responses import ApiResponse

from ...core.security import CurrentUser, verify_access_token

from ..dependencies import (

    AuthClientDep,

    ForecastingClientDep,

    UoWDep,

)

from .schemas import (

    PredictionHistoryResponseSchema,

    PredictionListItemSchema,

    PredictionRequestSchema,

    PredictionResponseSchema,

)

from .service import PredictionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])

def get_prediction_service(

    uow: UoWDep,

    auth_client: AuthClientDep,

    forecasting_client: ForecastingClientDep,

) -> PredictionService:

    return PredictionService(uow, auth_client, forecasting_client)

ServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]

@router.post("/", response_model=ApiResponse[PredictionResponseSchema])

async def create_prediction(

    request: Request,

    body: PredictionRequestSchema,

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

    service: ServiceDep,

):

    entity = await service.create_prediction(

        user_id=current_user.sub,

        features=body.features.model_dump(),

        horizon=body.horizon,

        ip_address=request.client.host if request.client else None,

        user_agent=request.headers.get("user-agent"),

    )

    response = ApiResponse(

        data=PredictionResponseSchema.model_validate(entity)

    )

    if entity.status == PredictionStatus.FAILED:

        return JSONResponse(

            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,

            content=response.model_dump(mode="json"),

        )

    return response

@router.get("/", response_model=ApiResponse[PredictionHistoryResponseSchema])

async def get_history(

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

    service: ServiceDep,

    limit: int = Query(default=20, ge=1, le=100),

    offset: int = Query(default=0, ge=0),

):

    entities, total = await service.get_user_predictions(

        user_id=current_user.sub,

        limit=limit,

        offset=offset,

    )

    items = [PredictionListItemSchema.from_entity(e) for e in entities]

    return ApiResponse(

        data=PredictionHistoryResponseSchema(

            items=items,

            total=total,

            limit=limit,

            offset=offset,

        )

    )

@router.get("/{prediction_id}", response_model=ApiResponse[PredictionResponseSchema])

async def get_prediction(

    prediction_id: UUID,

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

    service: ServiceDep,

):

    entity = await service.get_prediction(prediction_id, current_user.sub)

    return ApiResponse(

        data=PredictionResponseSchema.model_validate(entity)

    )

@router.delete("/{prediction_id}", response_model=ApiResponse[dict])

async def delete_prediction(

    prediction_id: UUID,

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

    service: ServiceDep,

):

    await service.delete_prediction(prediction_id, current_user.sub)

    return ApiResponse(data={"deleted": str(prediction_id)})
