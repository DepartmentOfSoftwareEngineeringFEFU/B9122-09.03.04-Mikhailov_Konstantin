from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.auth_service.app.dependencies import (
    get_admin_service,
    get_auth_service,
    get_current_user,
    get_profile_service,
)
from src.auth_service.app.middleware.rate_limiter import _get_rate_limiter
from src.auth_service.core.constants import UserRole
from src.auth_service.domain.entities import TokenPayload, UserEntity
from src.auth_service.main import create_app


class FakeRateLimiter:
    async def check_rate_limit(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
    ) -> None:
        return None

    async def reset(self, key: str) -> None:
        return None

    async def get_remaining(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int,
    ) -> tuple[int, int]:
        return max_attempts, 0


class FakeAuthService:
    def __init__(self):
        self.register_called_with = None
        self.login_called_with = None
        self.refresh_called_with = None
        self.logout_called_with = None

        self.user = UserEntity(
            uid=uuid4(),
            username="john",
            email="john@example.com",
            phone_number="+79001234567",
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True,
            two_factor_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        phone_number: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> UserEntity:
        self.register_called_with = {
            "username": username,
            "email": email,
            "password": password,
            "phone_number": phone_number,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id,
        }
        return self.user

    async def login(
        self,
        email: str,
        password: str,
        totp_code: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        self.login_called_with = {
            "email": email,
            "password": password,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id,
        }
        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
            "expires_in": 900,
        }

    async def login_2fa(
        self,
        auth_token: str,
        totp_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        return {
            "access_token": "access-token-2fa",
            "refresh_token": "refresh-token-2fa",
            "token_type": "bearer",
            "expires_in": 900,
        }

    async def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        self.refresh_called_with = {
            "refresh_token": refresh_token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "request_id": request_id,
        }
        return {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
            "expires_in": 900,
        }

    async def logout(
        self,
        refresh_token: str,
        token_payload: TokenPayload,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.logout_called_with = {
            "refresh_token": refresh_token,
            "token_payload": token_payload,
            "ip_address": ip_address,
            "request_id": request_id,
        }

    async def logout_all_devices(
        self,
        token_payload: TokenPayload,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        return None

    async def get_active_sessions(self, user_uid):
        return [
            {
                "device": "Chrome on Windows",
                "ip_address": "127.0.0.1",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_used_at": None,
            }
        ]

    async def resend_confirmation_email(
        self,
        email: str,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        return None

    async def confirm_email(
        self,
        token: str,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        return None

    async def request_password_reset(
        self,
        email: str,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        return None

    async def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> None:
        return None


class FakeProfileService:
    def __init__(self, user: UserEntity):
        self.user = user

    async def get_profile(self, user_uid):
        return self.user

    async def change_password(
        self,
        user_uid,
        current_password: str,
        new_password: str,
    ) -> None:
        return None

    async def change_username(
        self,
        user_uid,
        new_username: str,
    ) -> UserEntity:
        self.user.username = new_username
        return self.user

    async def change_phone(
        self,
        user_uid,
        new_phone: str | None,
    ) -> UserEntity:
        self.user.phone_number = new_phone
        return self.user

    async def setup_2fa(self, user_uid):
        return {
            "qr_code_base64": "base64-qr",
            "secret": "TOTPSECRET",
            "uri": "otpauth://totp/john@example.com?secret=TOTPSECRET",
        }

    async def confirm_2fa(self, user_uid, code: str) -> None:
        return None

    async def disable_2fa(
        self,
        user_uid,
        code: str,
        password: str,
    ) -> None:
        return None


class FakeAdminService:
    def __init__(self, users: list[UserEntity]):
        self.users = users

    async def list_users(
        self,
        offset: int = 0,
        limit: int = 50,
    ):
        return self.users[offset : offset + limit], len(self.users)

    async def get_user(self, user_uid):
        return self.users[0]

    async def change_role(
        self,
        user_uid,
        new_role,
        actor_uid=None,
        ip_address=None,
        request_id=None,
    ):
        self.users[0].role = new_role
        return self.users[0]

    async def delete_user(
        self,
        user_uid,
        actor_uid=None,
        ip_address=None,
        request_id=None,
    ) -> None:
        return None

    async def deactivate_user(
        self,
        user_uid,
        actor_uid=None,
        ip_address=None,
        request_id=None,
    ):
        self.users[0].is_active = False
        return self.users[0]

    async def activate_user(
        self,
        user_uid,
        actor_uid=None,
        ip_address=None,
        request_id=None,
    ):
        self.users[0].is_active = True
        return self.users[0]

    async def get_audit_log(
        self,
        user_uid=None,
        action=None,
        offset: int = 0,
        limit: int = 50,
    ):
        return [
            {
                "id": 1,
                "actor_uid": None,
                "target_uid": None,
                "action": "user.login.success",
                "details": None,
                "ip_address": "127.0.0.1",
                "user_agent": "pytest",
                "request_id": "req-1",
                "success": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ]


@pytest.fixture
def current_payload():
    now = datetime.now(timezone.utc)
    return TokenPayload(
        sub=uuid4(),
        role=UserRole.OWNER.value,
        token_type="access",
        exp=now + timedelta(minutes=15),
        iat=now,
        iss="auth-service",
        aud="auth-service-api",
        jti=uuid4(),
    )


@pytest.fixture
def fake_auth_service():
    return FakeAuthService()


@pytest.fixture
def client(fake_auth_service, current_payload):
    app = create_app()

    fake_profile_service = FakeProfileService(fake_auth_service.user)
    fake_admin_service = FakeAdminService([fake_auth_service.user])

    app.dependency_overrides[get_auth_service] = lambda: fake_auth_service
    app.dependency_overrides[get_profile_service] = lambda: fake_profile_service
    app.dependency_overrides[get_admin_service] = lambda: fake_admin_service
    app.dependency_overrides[get_current_user] = lambda: current_payload
    app.dependency_overrides[_get_rate_limiter] = lambda: FakeRateLimiter()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_register_route_returns_api_response(
    client,
    fake_auth_service,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "SecurePass1!",
            "phone_number": "+79001234567",
        },
        headers={
            "User-Agent": "pytest",
            "X-Request-ID": "req-register",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["username"] == "john"
    assert body["data"]["email"] == "john@example.com"
    assert body["data"]["is_active"] is True

    assert fake_auth_service.register_called_with["username"] == "john"
    assert fake_auth_service.register_called_with["email"] == "john@example.com"
    assert fake_auth_service.register_called_with["user_agent"] == "pytest"


def test_login_route_returns_tokens(
    client,
    fake_auth_service,
):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "john@example.com",
            "password": "SecurePass1!",
        },
        headers={
            "User-Agent": "pytest",
            "X-Request-ID": "req-login",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["access_token"] == "access-token"
    assert body["data"]["refresh_token"] == "refresh-token"
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["expires_in"] == 900

    assert fake_auth_service.login_called_with["email"] == "john@example.com"
    assert fake_auth_service.login_called_with["password"] == "SecurePass1!"


def test_login_2fa_route_returns_tokens(client):
    response = client.post(
        "/api/v1/auth/login/2fa",
        json={
            "auth_token": "auth-token",
            "totp_code": "123456",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["access_token"] == "access-token-2fa"
    assert body["data"]["refresh_token"] == "refresh-token-2fa"


def test_refresh_route_returns_new_tokens(
    client,
    fake_auth_service,
):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "old-refresh-token",
        },
        headers={
            "User-Agent": "pytest",
            "X-Request-ID": "req-refresh",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["data"]["access_token"] == "new-access-token"
    assert body["data"]["refresh_token"] == "new-refresh-token"

    assert fake_auth_service.refresh_called_with["refresh_token"] == (
        "old-refresh-token"
    )


def test_logout_route_returns_message(
    client,
    fake_auth_service,
):
    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": "refresh-token",
        },
        headers={
            "Authorization": "Bearer access-token",
            "X-Request-ID": "req-logout",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["message"] == "Logged out successfully"

    assert fake_auth_service.logout_called_with["refresh_token"] == "refresh-token"


def test_profile_me_route_returns_current_user_profile(client):
    response = client.get(
        "/api/v1/profile/me",
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["username"] == "john"
    assert body["data"]["email"] == "john@example.com"


def test_change_password_route_returns_message(client):
    response = client.patch(
        "/api/v1/profile/me/password",
        json={
            "current_password": "SecurePass1!",
            "new_password": "NewSecurePass1!",
        },
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["data"]["message"] == "Password changed successfully"


def test_change_username_route_returns_updated_user(client):
    response = client.patch(
        "/api/v1/profile/me/username",
        json={
            "new_username": "new_username",
        },
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["data"]["username"] == "new_username"


def test_setup_2fa_route_returns_qr_payload(client):
    response = client.post(
        "/api/v1/profile/me/2fa/setup",
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["data"]["qr_code_base64"] == "base64-qr"
    assert body["data"]["secret"] == "TOTPSECRET"
    assert body["data"]["uri"].startswith("otpauth://totp/")


def test_admin_list_users_route_returns_paginated_response(client):
    response = client.get(
        "/api/v1/admin/users",
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["total"] == 1
    assert body["data"]["offset"] == 0
    assert body["data"]["limit"] == 50
    assert body["data"]["has_more"] is False
    assert body["data"]["items"][0]["username"] == "new_username" or (
        body["data"]["items"][0]["username"] == "john"
    )


def test_admin_get_audit_log_route_returns_entries(client):
    response = client.get(
        "/api/v1/admin/audit-log",
        headers={
            "Authorization": "Bearer access-token",
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "success"
    assert body["data"][0]["action"] == "user.login.success"