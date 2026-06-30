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
from src.auth_service.core.exceptions import (
    InvalidCredentialsError,
    InsufficientPermissionsError,
)
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
    async def register(self, **kwargs):
        return UserEntity(
            uid=uuid4(),
            username=kwargs["username"],
            email=kwargs["email"],
            phone_number=kwargs.get("phone_number"),
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def login(self, **kwargs):
        raise InvalidCredentialsError()

    async def login_2fa(self, **kwargs):
        raise InvalidCredentialsError()

    async def refresh_tokens(self, **kwargs):
        raise InvalidCredentialsError()

    async def logout(self, **kwargs):
        return None

    async def logout_all_devices(self, **kwargs):
        return None

    async def get_active_sessions(self, user_uid):
        return []

    async def resend_confirmation_email(self, **kwargs):
        return None

    async def confirm_email(self, **kwargs):
        return None

    async def request_password_reset(self, **kwargs):
        return None

    async def reset_password(self, **kwargs):
        return None


class FakeProfileService:
    async def get_profile(self, user_uid):
        return UserEntity(
            uid=user_uid,
            username="john",
            email="john@example.com",
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def change_password(self, **kwargs):
        return None

    async def change_username(self, **kwargs):
        return UserEntity(
            uid=kwargs["user_uid"],
            username=kwargs["new_username"],
            email="john@example.com",
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def change_phone(self, **kwargs):
        return UserEntity(
            uid=kwargs["user_uid"],
            username="john",
            email="john@example.com",
            phone_number=kwargs["new_phone"],
            role=UserRole.USER,
            is_active=True,
            is_email_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def setup_2fa(self, user_uid):
        return {
            "qr_code_base64": "base64-qr",
            "secret": "TOTPSECRET",
            "uri": "otpauth://totp/john@example.com?secret=TOTPSECRET",
        }

    async def confirm_2fa(self, **kwargs):
        return None

    async def disable_2fa(self, **kwargs):
        return None


class FakeAdminService:
    async def list_users(self, offset: int = 0, limit: int = 50):
        return [], 0

    async def get_user(self, user_uid):
        raise InsufficientPermissionsError()

    async def change_role(self, **kwargs):
        raise InsufficientPermissionsError()

    async def delete_user(self, **kwargs):
        raise InsufficientPermissionsError()

    async def deactivate_user(self, **kwargs):
        raise InsufficientPermissionsError()

    async def activate_user(self, **kwargs):
        raise InsufficientPermissionsError()

    async def get_audit_log(self, **kwargs):
        return []


@pytest.fixture
def user_payload():
    now = datetime.now(timezone.utc)
    return TokenPayload(
        sub=uuid4(),
        role=UserRole.USER.value,
        token_type="access",
        exp=now + timedelta(minutes=15),
        iat=now,
        iss="auth-service",
        aud="auth-service-api",
        jti=uuid4(),
    )


@pytest.fixture
def app_with_user(user_payload):
    app = create_app()

    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    app.dependency_overrides[get_profile_service] = lambda: FakeProfileService()
    app.dependency_overrides[get_admin_service] = lambda: FakeAdminService()
    app.dependency_overrides[get_current_user] = lambda: user_payload
    app.dependency_overrides[_get_rate_limiter] = lambda: FakeRateLimiter()

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
def client(app_with_user):
    with TestClient(app_with_user) as test_client:
        yield test_client


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "not-an-email",
            "password": "SecurePass1!",
            "phone_number": "+79001234567",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


@pytest.mark.parametrize(
    "password",
    [
        "securepass1!",
        "SECUREPASS1!",
        "SecurePass!",
        "SecurePass1",
    ],
)
def test_register_rejects_weak_passwords(client, password):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": password,
            "phone_number": "+79001234567",
        },
    )

    assert response.status_code == 400

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "PasswordValidationError"
    assert body["error"]["message"] == "Password does not meet requirements"
    assert body["error"]["details"]

def test_register_rejects_too_short_password_with_validation_error(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "short1!",
            "phone_number": "+79001234567",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_register_rejects_invalid_phone(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john",
            "email": "john@example.com",
            "password": "SecurePass1!",
            "phone_number": "79001234567",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_register_rejects_username_with_spaces(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "john doe",
            "email": "john@example.com",
            "password": "SecurePass1!",
            "phone_number": "+79001234567",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_register_rejects_non_ascii_username(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "джон",
            "email": "john@example.com",
            "password": "SecurePass1!",
            "phone_number": "+79001234567",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_login_rejects_missing_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "john@example.com",
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_login_returns_api_error_for_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "john@example.com",
            "password": "WrongPass1!",
        },
    )

    assert response.status_code == 401

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "InvalidCredentialsError"
    assert body["error"]["message"] == "Invalid email or password"


@pytest.mark.parametrize(
    "totp_code",
    [
        "12345",
        "1234567",
        "abcdef",
        "",
    ],
)
def test_login_2fa_rejects_invalid_totp_code(client, totp_code):
    response = client.post(
        "/api/v1/auth/login/2fa",
        json={
            "auth_token": "auth-token",
            "totp_code": totp_code,
        },
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_refresh_rejects_missing_refresh_token(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={},
    )

    assert response.status_code == 422

    body = response.json()
    assert "detail" in body


def test_profile_me_without_authorization_returns_403_or_401():
    app = create_app()

    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    app.dependency_overrides[get_profile_service] = lambda: FakeProfileService()
    app.dependency_overrides[get_admin_service] = lambda: FakeAdminService()
    app.dependency_overrides[_get_rate_limiter] = lambda: FakeRateLimiter()

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/profile/me")

    app.dependency_overrides.clear()

    assert response.status_code in {401, 403}


def test_admin_users_with_user_role_returns_forbidden():
    now = datetime.now(timezone.utc)
    user_payload = TokenPayload(
        sub=uuid4(),
        role=UserRole.USER.value,
        token_type="access",
        exp=now + timedelta(minutes=15),
        iat=now,
        iss="auth-service",
        aud="auth-service-api",
        jti=uuid4(),
    )

    app = create_app()

    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    app.dependency_overrides[get_profile_service] = lambda: FakeProfileService()
    app.dependency_overrides[get_admin_service] = lambda: FakeAdminService()
    app.dependency_overrides[get_current_user] = lambda: user_payload
    app.dependency_overrides[_get_rate_limiter] = lambda: FakeRateLimiter()

    with TestClient(app) as test_client:
        response = test_client.get(
            "/api/v1/admin/users",
            headers={"Authorization": "Bearer access-token"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 403

    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "InsufficientPermissionsError"