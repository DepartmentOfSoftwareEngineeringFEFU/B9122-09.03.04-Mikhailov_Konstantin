from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.auth_service.app.dependencies import get_current_user
from src.auth_service.app.internal.router import verify_internal_token
from src.auth_service.core.exceptions import TokenRevokedException
from src.auth_service.domain.entities import TokenPayload


pytestmark = pytest.mark.asyncio


async def test_get_current_user_returns_payload_for_valid_token(
    uow,
    token_service,
    active_user,
):
    token = token_service.create_access_token(active_user)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    payload = await get_current_user(
        credentials=credentials,
        token_service=token_service,
        uow=uow,
    )

    assert payload.sub == active_user.uid
    assert payload.token_type == "access"


async def test_get_current_user_rejects_blacklisted_jti(
    uow,
    token_service,
    active_user,
):
    token = token_service.create_access_token(active_user)
    payload = token_service.decode_access_token(token)

    await uow.token_blacklist.blacklist_token(
        jti=str(payload.jti),
        user_uid=payload.sub,
        expires_at=payload.exp,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(TokenRevokedException):
        await get_current_user(
            credentials=credentials,
            token_service=token_service,
            uow=uow,
        )


async def test_get_current_user_rejects_user_wide_revoked_token(
    uow,
    token_service,
    active_user,
):
    token = token_service.create_access_token(active_user)
    payload = token_service.decode_access_token(token)

    await uow.token_blacklist.blacklist_all_for_user(
        user_uid=payload.sub,
        before=payload.iat + timedelta(seconds=1),
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    with pytest.raises(TokenRevokedException):
        await get_current_user(
            credentials=credentials,
            token_service=token_service,
            uow=uow,
        )


async def test_get_current_user_allows_token_issued_after_user_revocation(
    uow,
    token_service,
    active_user,
):
    token = token_service.create_access_token(active_user)
    payload = token_service.decode_access_token(token)

    await uow.token_blacklist.blacklist_all_for_user(
        user_uid=payload.sub,
        before=payload.iat - timedelta(seconds=1),
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    result = await get_current_user(
        credentials=credentials,
        token_service=token_service,
        uow=uow,
    )

    assert result.sub == active_user.uid


async def test_verify_internal_token_accepts_valid_token(monkeypatch):
    from src.auth_service.app.internal import router as internal_router

    monkeypatch.setattr(
        internal_router.settings,
        "INTERNAL_SERVICE_TOKEN",
        "internal-token-for-tests",
    )

    result = await verify_internal_token(
        x_internal_token="internal-token-for-tests",
    )

    assert result == "internal-token-for-tests"


async def test_verify_internal_token_rejects_invalid_token(monkeypatch):
    from src.auth_service.app.internal import router as internal_router

    monkeypatch.setattr(
        internal_router.settings,
        "INTERNAL_SERVICE_TOKEN",
        "internal-token-for-tests",
    )

    with pytest.raises(HTTPException) as exc_info:
        await verify_internal_token(
            x_internal_token="wrong-token",
        )

    assert exc_info.value.status_code == 401