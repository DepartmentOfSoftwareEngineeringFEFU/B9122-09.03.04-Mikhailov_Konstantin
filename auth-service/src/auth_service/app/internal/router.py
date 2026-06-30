from uuid import UUID
from typing import Annotated
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Header, status

from src.auth_service.api.responses import ApiResponse
from src.auth_service.app.dependencies import get_uow
from src.auth_service.config import settings
from src.auth_service.core.protocols import UnitOfWorkProtocol
from src.auth_service.domain.entities import UserEntity
from src.auth_service.core.security import secure_compare

router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
    include_in_schema=settings.ENVIRONMENT.value != "production",
)

class TokenStatusRequest(BaseModel):
    user_uid: UUID
    jti: str = Field(min_length=1)
    issued_at: datetime


class TokenStatusResponse(BaseModel):
    revoked: bool
    reason: str | None = None


async def verify_internal_token(
    x_internal_token: str = Header(..., alias="X-Internal-Token"),
) -> str:
    """Проверка внутреннего токена для межсервисной коммуникации"""
    if not secure_compare(x_internal_token, settings.INTERNAL_SERVICE_TOKEN):
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
    summary="[Internal] Проверить список токенов по jti",
    dependencies=[Depends(verify_internal_token)],
)
async def check_token_blacklist(
    jti_list: list[str],
    uow: Annotated[UnitOfWorkProtocol, Depends(get_uow)],
):
    """
    Проверяет, какие jti access-токенов находятся в blacklist.
    Может использоваться main-backend для кэширования blacklist-статуса.
    """
    async with uow:
        blacklisted = await uow.token_blacklist.are_blacklisted(jti_list)

    return ApiResponse(data={"blacklisted": blacklisted})


@router.post(
    "/tokens/check",
    response_model=ApiResponse[TokenStatusResponse],
    summary="[Internal] Проверить статус access token",
    dependencies=[Depends(verify_internal_token)],
)
async def check_token_status(
    data: TokenStatusRequest,
    uow: Annotated[UnitOfWorkProtocol, Depends(get_uow)],
):
    """
    Проверяет access token по двум механизмам:
    1. точечный blacklist по jti;
    2. user-wide revocation по user_uid + issued_at.

    Используется main-backend после локальной JWT-валидации.
    """
    async with uow:
        if await uow.token_blacklist.is_blacklisted(data.jti):
            return ApiResponse(
                data=TokenStatusResponse(
                    revoked=True,
                    reason="token_blacklisted",
                )
            )

        if await uow.token_blacklist.is_user_tokens_revoked(
            user_uid=data.user_uid,
            issued_at=data.issued_at,
        ):
            return ApiResponse(
                data=TokenStatusResponse(
                    revoked=True,
                    reason="user_tokens_revoked",
                )
            )

    return ApiResponse(
        data=TokenStatusResponse(
            revoked=False,
            reason=None,
        )
    )
