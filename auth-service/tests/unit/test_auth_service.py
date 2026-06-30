from datetime import datetime, timedelta, timezone

import pytest

from src.auth_service.core.constants import AuditAction
from src.auth_service.core.exceptions import (
    AccountNotActiveError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTwoFactorCodeError,
    TokenRevokedException,
    UserAlreadyExistsError,
)
from src.auth_service.external.security.refresh_token_service import (
    RefreshTokenService,
)


pytestmark = pytest.mark.asyncio


async def test_register_creates_auto_verified_user_in_dev(
    auth_service,
    uow,
    monkeypatch,
):
    from src.auth_service.app.auth import service as auth_module

    monkeypatch.setattr(auth_module.settings, "AUTO_VERIFY_EMAIL_IN_DEV", True)
    monkeypatch.setattr(auth_module.settings, "ENVIRONMENT", "development")

    user = await auth_service.register(
        username="john",
        email="John@Example.com",
        password="SecurePass1!",
        phone_number="+79001234567",
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-1",
    )

    assert user.email == "John@Example.com"
    assert user.is_active is True
    assert user.is_email_verified is True
    assert uow.committed is True

    assert len(uow.audit.entries) == 1
    assert uow.audit.entries[0]["action"] == AuditAction.USER_REGISTERED.value
    assert uow.audit.entries[0]["details"]["auto_verified"] is True


async def test_register_rejects_duplicate_email(
    auth_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    with pytest.raises(UserAlreadyExistsError):
        await auth_service.register(
            username="other",
            email=active_user.email,
            password="SecurePass1!",
        )


async def test_login_success_issues_access_and_refresh_tokens(
    auth_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    tokens = await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-login",
    )

    assert tokens["access_token"] == f"access:{active_user.uid}"
    assert tokens["token_type"] == "bearer"
    assert tokens["refresh_token"]
    assert tokens["expires_in"] > 0

    assert len(uow.refresh_sessions.sessions) == 1
    assert uow.audit.entries[-1]["action"] == AuditAction.USER_LOGIN_SUCCESS.value
    assert uow.committed is True


async def test_login_with_unknown_email_raises_invalid_credentials(
    auth_service,
    uow,
):
    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            email="missing@example.com",
            password="SecurePass1!",
            ip_address="127.0.0.1",
        )

    assert uow.audit.entries[-1]["action"] == AuditAction.USER_LOGIN_FAILED.value
    assert uow.audit.entries[-1]["success"] is False
    assert uow.audit.entries[-1]["details"]["reason"] == "user_not_found"


async def test_login_with_wrong_password_raises_invalid_credentials(
    auth_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    with pytest.raises(InvalidCredentialsError):
        await auth_service.login(
            email=active_user.email,
            password="WrongPass1!",
            ip_address="127.0.0.1",
        )

    assert uow.audit.entries[-1]["action"] == AuditAction.USER_LOGIN_FAILED.value
    assert uow.audit.entries[-1]["success"] is False
    assert uow.audit.entries[-1]["details"]["reason"] == "invalid_password"


async def test_login_rejects_inactive_user(
    auth_service,
    uow,
    inactive_user,
):
    await uow.users.create(inactive_user)

    with pytest.raises(AccountNotActiveError):
        await auth_service.login(
            email=inactive_user.email,
            password="SecurePass1!",
        )

    assert uow.audit.entries[-1]["details"]["reason"] == "account_not_active"


async def test_login_with_2fa_enabled_returns_auth_token(
    auth_service,
    uow,
    active_user,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    result = await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )

    assert result["requires_2fa"] is True
    assert result["auth_token"] == f"auth:{active_user.uid}"
    assert result["expires_in"] > 0

    assert len(uow.refresh_sessions.sessions) == 0


async def test_login_2fa_success_issues_tokens(
    auth_service,
    uow,
    active_user,
    token_service,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    auth_token = token_service.create_auth_token(active_user)

    tokens = await auth_service.login_2fa(
        auth_token=auth_token,
        totp_code="123456",
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-2fa",
    )

    assert tokens["access_token"] == f"access:{active_user.uid}"
    assert tokens["refresh_token"]
    assert len(uow.refresh_sessions.sessions) == 1
    assert uow.audit.entries[-1]["action"] == AuditAction.USER_LOGIN_SUCCESS.value


async def test_login_2fa_rejects_wrong_code(
    auth_service,
    uow,
    active_user,
    token_service,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    auth_token = token_service.create_auth_token(active_user)

    with pytest.raises(InvalidTwoFactorCodeError):
        await auth_service.login_2fa(
            auth_token=auth_token,
            totp_code="000000",
        )

    assert uow.audit.entries[-1]["action"] == AuditAction.TWO_FACTOR_FAILED.value
    assert uow.audit.entries[-1]["success"] is False


async def test_refresh_tokens_rotates_refresh_session(
    auth_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    login_tokens = await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )

    old_refresh = login_tokens["refresh_token"]
    old_hash = RefreshTokenService.hash_token(old_refresh)

    refresh_result = await auth_service.refresh_tokens(
        refresh_token=old_refresh,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-refresh",
    )

    assert refresh_result["access_token"] == f"access:{active_user.uid}"
    assert refresh_result["refresh_token"] != old_refresh

    old_session = await uow.refresh_sessions.get_by_token_hash(old_hash)
    assert old_session.is_revoked is True
    assert old_session.replaced_by is not None

    assert len(uow.refresh_sessions.sessions) == 2
    assert uow.audit.entries[-1]["action"] == AuditAction.TOKEN_REFRESHED.value


async def test_refresh_token_reuse_revokes_all_user_sessions_and_tokens(
    auth_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    login_tokens = await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )
    old_refresh = login_tokens["refresh_token"]

    await auth_service.refresh_tokens(refresh_token=old_refresh)

    with pytest.raises(TokenRevokedException):
        await auth_service.refresh_tokens(refresh_token=old_refresh)

    assert all(
        session.is_revoked for session in uow.refresh_sessions.sessions.values()
    )
    assert active_user.uid in uow.token_blacklist.user_revocations
    assert uow.audit.entries[-1]["details"]["reason"] == (
        "refresh_token_reuse_detected"
    )


async def test_logout_revokes_refresh_and_blacklists_current_access_token(
    auth_service,
    uow,
    active_user,
    access_payload,
):
    await uow.users.create(active_user)

    login_tokens = await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )

    refresh_token = login_tokens["refresh_token"]
    refresh_hash = RefreshTokenService.hash_token(refresh_token)

    await auth_service.logout(
        refresh_token=refresh_token,
        token_payload=access_payload,
        ip_address="127.0.0.1",
        request_id="req-logout",
    )

    session = await uow.refresh_sessions.get_by_token_hash(refresh_hash)
    assert session.is_revoked is True

    assert str(access_payload.jti) in uow.token_blacklist.blacklisted_jti
    assert uow.audit.entries[-1]["action"] == AuditAction.USER_LOGOUT.value


async def test_logout_rejects_unknown_refresh_token(
    auth_service,
    active_user,
    access_payload,
):
    with pytest.raises(InvalidTokenError):
        await auth_service.logout(
            refresh_token="unknown-refresh-token",
            token_payload=access_payload,
        )


async def test_logout_all_revokes_all_sessions_and_user_access_tokens(
    auth_service,
    uow,
    active_user,
    access_payload,
):
    await uow.users.create(active_user)

    await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )
    await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )

    await auth_service.logout_all_devices(
        token_payload=access_payload,
        ip_address="127.0.0.1",
        request_id="req-logout-all",
    )

    assert all(
        session.is_revoked for session in uow.refresh_sessions.sessions.values()
    )
    assert active_user.uid in uow.token_blacklist.user_revocations
    assert uow.audit.entries[-1]["action"] == AuditAction.USER_LOGOUT_ALL.value


async def test_reset_password_changes_password_and_revokes_sessions(
    auth_service,
    uow,
    active_user,
    url_token_service,
    hasher,
):
    await uow.users.create(active_user)

    await auth_service.login(
        email=active_user.email,
        password="SecurePass1!",
    )

    token = url_token_service.create_token(
        data={"email": active_user.email, "uid": str(active_user.uid)},
        purpose="password_reset",
    )

    await auth_service.reset_password(
        token=token,
        new_password="NewSecurePass1!",
        ip_address="127.0.0.1",
        request_id="req-reset",
    )

    updated = await uow.users.get_by_id(active_user.uid)
    assert hasher.verify("NewSecurePass1!", updated.password_hash)

    assert all(
        session.is_revoked for session in uow.refresh_sessions.sessions.values()
    )
    assert active_user.uid in uow.token_blacklist.user_revocations
    assert uow.audit.entries[-1]["action"] == (
        AuditAction.PASSWORD_RESET_COMPLETED.value
    )