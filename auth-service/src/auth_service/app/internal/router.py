from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.auth_service.api.responses import ApiResponse
from src.auth_service.app.dependencies import get_uow
from src.auth_service.config import settings
from src.auth_service.core.protocols import UnitOfWorkProtocol
from src.auth_service.domain.entities import UserEntity

router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
    include_in_schema=settings.ENVIRONMENT.value != "production",
)


async def verify_internal_token(
    x_internal_token: str = Header(..., alias="X-Internal-Token"),
) -> str:
    """Проверка внутреннего токена для межсервисной коммуникации"""
    if x_internal_token != settings.INTERNAL_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service token",
        )
    return x_internal_token


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse[dict],
    summary="[Internal] Получить пользователя по ID",
    dependencies=[Depends(verify_internal_token)],
)
async def get_user_by_id(
    user_id: UUID,
    uow: Annotated[UnitOfWorkProtocol, Depends(get_uow)],
):
    """
    Внутренний endpoint для main-backend.
    Возвращает публичные данные пользователя.
    """
    async with uow:
        user = await uow.users.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Возвращаем только необходимые поля (без password_hash!)
    return ApiResponse(
        data={
            "uid": str(user.uid),
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_email_verified": user.is_email_verified,
            "two_factor_enabled": user.two_factor_enabled,
            "created_at": user.created_at.isoformat(),
        }
    )


@router.post(
    "/tokens/check-blacklist",
    response_model=ApiResponse[dict],
    summary="[Internal] Проверить, отозван ли токен",
    dependencies=[Depends(verify_internal_token)],
)
async def check_token_blacklist(
    jti_list: list[str],
    uow: Annotated[UnitOfWorkProtocol, Depends(get_uow)],
):
    """
    Проверяет, есть ли jti токенов в blacklist.
    main-backend может кэшировать результат в Redis.
    """
    # TODO: добавить метод в TokenBlacklistProtocol
    # is_blacklisted = await uow.token_blacklist.are_blacklisted(jti_list)
    return ApiResponse(data={"blacklisted": []})