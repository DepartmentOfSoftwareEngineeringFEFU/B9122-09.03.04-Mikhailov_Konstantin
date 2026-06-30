from datetime import datetime, timezone

import pytest

from src.auth_service.core.constants import AuditAction, UserRole
from src.auth_service.core.exceptions import (
    AuthorizationError,
    UserNotFoundError,
)
from src.auth_service.domain.entities import UserEntity
from src.auth_service.external.security.refresh_token_service import (
    RefreshTokenService,
)


pytestmark = pytest.mark.asyncio


async def test_list_users_returns_users_and_total(
    admin_service,
    uow,
    active_user,
    admin_user,
):
    await uow.users.create(active_user)
    await uow.users.create(admin_user)

    users, total = await admin_service.list_users(offset=0, limit=10)

    assert total == 2
    assert len(users) == 2


async def test_get_user_returns_user(
    admin_service,
    uow,
    active_user,
):
    await uow.users.create(active_user)

    result = await admin_service.get_user(active_user.uid)

    assert result.uid == active_user.uid
    assert result.email == active_user.email


async def test_get_user_raises_when_not_found(
    admin_service,
    active_user,
):
    with pytest.raises(UserNotFoundError):
        await admin_service.get_user(active_user.uid)


async def test_change_role_updates_role_and_revokes_access_tokens(
    admin_service,
    uow,
    active_user,
    owner_user,
):
    await uow.users.create(active_user)
    await uow.users.create(owner_user)

    result = await admin_service.change_role(
        user_uid=active_user.uid,
        new_role=UserRole.ADMIN,
        actor_uid=owner_user.uid,
        ip_address="127.0.0.1",
        request_id="req-role",
    )

    assert result.role == UserRole.ADMIN
    assert active_user.uid in uow.token_blacklist.user_revocations

    assert uow.audit.entries[-1]["action"] == AuditAction.ROLE_CHANGED.value
    assert uow.audit.entries[-1]["actor_uid"] == owner_user.uid
    assert uow.audit.entries[-1]["target_uid"] == active_user.uid
    assert uow.audit.entries[-1]["details"]["old_role"] == UserRole.USER.value
    assert uow.audit.entries[-1]["details"]["new_role"] == UserRole.ADMIN.value
    assert "access_tokens_revoked_before" in uow.audit.entries[-1]["details"]


async def test_change_role_rejects_assigning_owner_role(
    admin_service,
    uow,
    active_user,
    owner_user,
):
    await uow.users.create(active_user)

    with pytest.raises(AuthorizationError):
        await admin_service.change_role(
            user_uid=active_user.uid,
            new_role=UserRole.OWNER,
            actor_uid=owner_user.uid,
        )


async def test_change_role_rejects_changing_owner_role(
    admin_service,
    uow,
    owner_user,
    admin_user,
):
    await uow.users.create(owner_user)

    with pytest.raises(AuthorizationError):
        await admin_service.change_role(
            user_uid=owner_user.uid,
            new_role=UserRole.USER,
            actor_uid=admin_user.uid,
        )


async def test_change_role_rejects_self_role_change(
    admin_service,
    uow,
    admin_user,
):
    await uow.users.create(admin_user)

    with pytest.raises(AuthorizationError):
        await admin_service.change_role(
            user_uid=admin_user.uid,
            new_role=UserRole.USER,
            actor_uid=admin_user.uid,
        )


async def test_delete_user_deletes_user_and_revokes_tokens(
    admin_service,
    uow,
    active_user,
    owner_user,
):
    await uow.users.create(active_user)

    session = RefreshTokenService.create_session(
        token="refresh-token-1",
        user_uid=active_user.uid,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    await uow.refresh_sessions.create(session)

    await admin_service.delete_user(
        user_uid=active_user.uid,
        actor_uid=owner_user.uid,
        ip_address="127.0.0.1",
        request_id="req-delete",
    )

    deleted = await uow.users.get_by_id(active_user.uid)

    assert deleted is None
    assert all(
        session.is_revoked
        for session in uow.refresh_sessions.sessions.values()
    )
    assert active_user.uid in uow.token_blacklist.user_revocations

    assert uow.audit.entries[-1]["action"] == AuditAction.USER_DELETED.value
    assert uow.audit.entries[-1]["actor_uid"] == owner_user.uid
    assert uow.audit.entries[-1]["target_uid"] == active_user.uid


async def test_delete_user_rejects_owner_delete(
    admin_service,
    uow,
    owner_user,
):
    await uow.users.create(owner_user)

    with pytest.raises(AuthorizationError):
        await admin_service.delete_user(
            user_uid=owner_user.uid,
            actor_uid=None,
        )


async def test_delete_user_rejects_self_delete(
    admin_service,
    uow,
    admin_user,
):
    await uow.users.create(admin_user)

    with pytest.raises(AuthorizationError):
        await admin_service.delete_user(
            user_uid=admin_user.uid,
            actor_uid=admin_user.uid,
        )


async def test_deactivate_user_deactivates_and_revokes_tokens(
    admin_service,
    uow,
    active_user,
    admin_user,
):
    await uow.users.create(active_user)

    session = RefreshTokenService.create_session(
        token="refresh-token-1",
        user_uid=active_user.uid,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    await uow.refresh_sessions.create(session)

    result = await admin_service.deactivate_user(
        user_uid=active_user.uid,
        actor_uid=admin_user.uid,
        ip_address="127.0.0.1",
        request_id="req-deactivate",
    )

    assert result.is_active is False
    assert all(
        session.is_revoked
        for session in uow.refresh_sessions.sessions.values()
    )
    assert active_user.uid in uow.token_blacklist.user_revocations

    assert uow.audit.entries[-1]["action"] == AuditAction.USER_DEACTIVATED.value
    assert uow.audit.entries[-1]["details"]["revoked_sessions"] == 1
    assert "access_tokens_revoked_before" in uow.audit.entries[-1]["details"]


async def test_deactivate_user_rejects_owner(
    admin_service,
    uow,
    owner_user,
):
    await uow.users.create(owner_user)

    with pytest.raises(AuthorizationError):
        await admin_service.deactivate_user(
            user_uid=owner_user.uid,
        )


async def test_activate_user_activates_user(
    admin_service,
    uow,
    active_user,
    admin_user,
):
    active_user.is_active = False
    await uow.users.create(active_user)

    result = await admin_service.activate_user(
        user_uid=active_user.uid,
        actor_uid=admin_user.uid,
        ip_address="127.0.0.1",
        request_id="req-activate",
    )

    assert result.is_active is True
    assert uow.audit.entries[-1]["action"] == AuditAction.USER_ACTIVATED.value
    assert uow.audit.entries[-1]["actor_uid"] == admin_user.uid
    assert uow.audit.entries[-1]["target_uid"] == active_user.uid


async def test_get_audit_log_returns_all_entries(
    admin_service,
    uow,
    active_user,
):
    await uow.audit.log(
        action=AuditAction.USER_REGISTERED.value,
        actor_uid=active_user.uid,
        target_uid=active_user.uid,
    )
    await uow.audit.log(
        action=AuditAction.USER_LOGIN_SUCCESS.value,
        actor_uid=active_user.uid,
    )

    entries = await admin_service.get_audit_log()

    assert len(entries) == 2


async def test_get_audit_log_filters_by_user_uid(
    admin_service,
    uow,
    active_user,
    admin_user,
):
    await uow.audit.log(
        action=AuditAction.USER_REGISTERED.value,
        actor_uid=active_user.uid,
        target_uid=active_user.uid,
    )
    await uow.audit.log(
        action=AuditAction.USER_LOGIN_SUCCESS.value,
        actor_uid=admin_user.uid,
    )

    entries = await admin_service.get_audit_log(
        user_uid=active_user.uid,
    )

    assert len(entries) == 1
    assert entries[0]["actor_uid"] == active_user.uid


async def test_get_audit_log_filters_by_action(
    admin_service,
    uow,
    active_user,
):
    await uow.audit.log(
        action=AuditAction.USER_REGISTERED.value,
        actor_uid=active_user.uid,
    )
    await uow.audit.log(
        action=AuditAction.USER_LOGIN_SUCCESS.value,
        actor_uid=active_user.uid,
    )

    entries = await admin_service.get_audit_log(
        action=AuditAction.USER_LOGIN_SUCCESS.value,
    )

    assert len(entries) == 1
    assert entries[0]["action"] == AuditAction.USER_LOGIN_SUCCESS.value