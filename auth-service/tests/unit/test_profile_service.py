import pytest

from src.auth_service.core.constants import AuditAction
from src.auth_service.core.exceptions import (
    InvalidCredentialsError,
    InvalidTwoFactorCodeError,
    SamePasswordError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotEnabledError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.auth_service.domain.entities import UserEntity
from src.auth_service.external.security.refresh_token_service import (
    RefreshTokenService,
)


pytestmark = pytest.mark.asyncio


async def test_get_profile_returns_user(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await profile_service.get_profile(active_user.uid)

    assert result.uid == active_user.uid
    assert result.email == active_user.email


async def test_get_profile_raises_when_user_not_found(
    profile_service,
    active_user,
):
    with pytest.raises(UserNotFoundError):
        await profile_service.get_profile(active_user.uid)


async def test_change_password_updates_password_and_revokes_sessions(
    profile_service,
    uow,
    active_user,
    hasher,
):
    await uow.users.create(active_user)

    session = RefreshTokenService.create_session(
        token="refresh-token-1",
        user_uid=active_user.uid,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    await uow.refresh_sessions.create(session)

    await profile_service.change_password(
        user_uid=active_user.uid,
        current_password="SecurePass1!",
        new_password="NewSecurePass1!",
    )

    updated = await uow.users.get_by_id(active_user.uid)

    assert hasher.verify("NewSecurePass1!", updated.password_hash)
    assert all(
        session.is_revoked
        for session in uow.refresh_sessions.sessions.values()
    )
    assert active_user.uid in uow.token_blacklist.user_revocations
    assert uow.committed is True

    assert uow.audit.entries[-1]["action"] == AuditAction.PASSWORD_CHANGED.value


async def test_change_password_rejects_wrong_current_password(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    with pytest.raises(InvalidCredentialsError):
        await profile_service.change_password(
            user_uid=active_user.uid,
            current_password="WrongPass1!",
            new_password="NewSecurePass1!",
        )


async def test_change_password_rejects_same_password(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    with pytest.raises(SamePasswordError):
        await profile_service.change_password(
            user_uid=active_user.uid,
            current_password="SecurePass1!",
            new_password="SecurePass1!",
        )


async def test_change_username_updates_username(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await profile_service.change_username(
        user_uid=active_user.uid,
        new_username="new_username",
    )

    assert result.username == "new_username"
    assert uow.committed is True


async def test_change_username_returns_user_when_username_is_same(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await profile_service.change_username(
        user_uid=active_user.uid,
        new_username=active_user.username,
    )

    assert result.uid == active_user.uid
    assert result.username == active_user.username


async def test_change_username_rejects_duplicate_username(
    profile_service,
    uow,
    active_user,
    hasher,
):
    await uow.users.create(active_user)

    another_user = UserEntity(
        username="busy_username",
        email="busy@example.com",
        password_hash=hasher.hash("SecurePass1!"),
        is_active=True,
        is_email_verified=True,
    )
    await uow.users.create(another_user)

    with pytest.raises(UserAlreadyExistsError):
        await profile_service.change_username(
            user_uid=active_user.uid,
            new_username="busy_username",
        )


async def test_change_phone_updates_phone(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await profile_service.change_phone(
        user_uid=active_user.uid,
        new_phone="+79009998877",
    )

    assert result.phone_number == "+79009998877"
    assert uow.committed is True


async def test_change_phone_can_remove_phone(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await profile_service.change_phone(
        user_uid=active_user.uid,
        new_phone=None,
    )

    assert result.phone_number is None
    assert uow.committed is True


async def test_change_phone_rejects_duplicate_phone(
    profile_service,
    uow,
    active_user,
    hasher,
):
    await uow.users.create(active_user)

    another_user = UserEntity(
        username="other",
        email="other@example.com",
        password_hash=hasher.hash("SecurePass1!"),
        phone_number="+79990001122",
        is_active=True,
        is_email_verified=True,
    )
    await uow.users.create(another_user)

    with pytest.raises(UserAlreadyExistsError):
        await profile_service.change_phone(
            user_uid=active_user.uid,
            new_phone="+79990001122",
        )


async def test_setup_2fa_stores_encrypted_secret_and_returns_qr_data(
    profile_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await profile_service.setup_2fa(active_user.uid)

    updated = await uow.users.get_by_id(active_user.uid)

    assert updated.totp_secret == "encrypted:TOTPSECRET"
    assert updated.two_factor_enabled is False

    assert result["qr_code_base64"] == "base64-qr"
    assert result["secret"] == "TOTPSECRET"
    assert result["uri"].startswith("otpauth://totp/")
    assert uow.committed is True


async def test_setup_2fa_rejects_when_already_enabled(
    profile_service,
    uow,
    active_user,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    with pytest.raises(TwoFactorAlreadyEnabledError):
        await profile_service.setup_2fa(active_user.uid)


async def test_confirm_2fa_enables_two_factor(
    profile_service,
    uow,
    active_user,
):
    active_user.totp_secret = "encrypted:TOTPSECRET"
    active_user.two_factor_enabled = False
    await uow.users.create(active_user)

    await profile_service.confirm_2fa(
        user_uid=active_user.uid,
        code="123456",
    )

    updated = await uow.users.get_by_id(active_user.uid)

    assert updated.two_factor_enabled is True
    assert uow.committed is True


async def test_confirm_2fa_rejects_when_secret_missing(
    profile_service,
    uow,
    active_user,
):
    active_user.totp_secret = None
    active_user.two_factor_enabled = False
    await uow.users.create(active_user)

    with pytest.raises(TwoFactorNotEnabledError):
        await profile_service.confirm_2fa(
            user_uid=active_user.uid,
            code="123456",
        )


async def test_confirm_2fa_rejects_wrong_code(
    profile_service,
    uow,
    active_user,
):
    active_user.totp_secret = "encrypted:TOTPSECRET"
    active_user.two_factor_enabled = False
    await uow.users.create(active_user)

    with pytest.raises(InvalidTwoFactorCodeError):
        await profile_service.confirm_2fa(
            user_uid=active_user.uid,
            code="000000",
        )


async def test_disable_2fa_disables_two_factor_and_clears_secret(
    profile_service,
    uow,
    active_user,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    await profile_service.disable_2fa(
        user_uid=active_user.uid,
        code="123456",
        password="SecurePass1!",
    )

    updated = await uow.users.get_by_id(active_user.uid)

    assert updated.two_factor_enabled is False
    assert updated.totp_secret is None
    assert uow.committed is True


async def test_disable_2fa_rejects_when_not_enabled(
    profile_service,
    uow,
    active_user,
):
    active_user.two_factor_enabled = False
    active_user.totp_secret = None
    await uow.users.create(active_user)

    with pytest.raises(TwoFactorNotEnabledError):
        await profile_service.disable_2fa(
            user_uid=active_user.uid,
            code="123456",
            password="SecurePass1!",
        )


async def test_disable_2fa_rejects_wrong_password(
    profile_service,
    uow,
    active_user,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    with pytest.raises(InvalidCredentialsError):
        await profile_service.disable_2fa(
            user_uid=active_user.uid,
            code="123456",
            password="WrongPass1!",
        )


async def test_disable_2fa_rejects_wrong_code(
    profile_service,
    uow,
    active_user,
):
    active_user.two_factor_enabled = True
    active_user.totp_secret = "encrypted:TOTPSECRET"
    await uow.users.create(active_user)

    with pytest.raises(InvalidTwoFactorCodeError):
        await profile_service.disable_2fa(
            user_uid=active_user.uid,
            code="000000",
            password="SecurePass1!",
        )