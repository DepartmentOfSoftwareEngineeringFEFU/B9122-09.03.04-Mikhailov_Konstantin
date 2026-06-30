from datetime import datetime, timedelta, timezone

import pytest
from cryptography.fernet import Fernet

from src.auth_service.core.constants import TokenPurpose, TokenType, UserRole
from src.auth_service.core.exceptions import (
    InvalidTokenError,
    PasswordValidationError,
    TokenExpiredError,
)
from src.auth_service.core.security import (
    PasswordValidator,
    PhoneValidator,
    URLSafeTokenService,
    secure_compare,
)
from src.auth_service.domain.entities import UserEntity
from src.auth_service.external.security.jwt_service import JWTService
from src.auth_service.external.security.refresh_token_service import (
    RefreshTokenService,
)
from src.auth_service.external.security.totp_service import TOTPService


def test_password_validator_accepts_strong_password():
    validator = PasswordValidator()

    validator.validate("SecurePass1!")


@pytest.mark.parametrize(
    "password",
    [
        "short1!",
        "securepass1!",
        "SECUREPASS1!",
        "SecurePass!",
        "SecurePass1",
    ],
)
def test_password_validator_rejects_weak_passwords(password):
    validator = PasswordValidator()

    with pytest.raises(PasswordValidationError):
        validator.validate(password)


@pytest.mark.parametrize(
    ("raw_phone", "expected"),
    [
        ("+79001234567", "+79001234567"),
        ("+7 900 123 45 67", "+79001234567"),
        ("+7-900-123-45-67", "+79001234567"),
    ],
)
def test_phone_validator_normalizes_valid_phone(raw_phone, expected):
    assert PhoneValidator.validate(raw_phone) == expected


@pytest.mark.parametrize(
    "phone",
    [
        "79001234567",
        "+09001234567",
        "+123",
        "phone",
        "",
    ],
)
def test_phone_validator_rejects_invalid_phone(phone):
    with pytest.raises(ValueError):
        PhoneValidator.validate(phone)


def test_secure_compare_returns_true_for_equal_strings():
    assert secure_compare("secret", "secret") is True


def test_secure_compare_returns_false_for_different_strings():
    assert secure_compare("secret", "other") is False


def test_refresh_token_service_generates_token_and_hash():
    token = RefreshTokenService.generate_token()
    token_hash = RefreshTokenService.hash_token(token)

    assert token
    assert len(token_hash) == 64
    assert token_hash == RefreshTokenService.hash_token(token)
    assert token_hash != RefreshTokenService.hash_token(token + "x")


def test_refresh_token_service_creates_session(monkeypatch):
    from src.auth_service.external.security import refresh_token_service as module

    monkeypatch.setattr(module.settings, "REFRESH_TOKEN_EXPIRE_DAYS", 7)

    user_uid = UserEntity().uid
    session = RefreshTokenService.create_session(
        token="refresh-token",
        user_uid=user_uid,
        ip_address="127.0.0.1",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
    )

    assert session.user_uid == user_uid
    assert session.token_hash == RefreshTokenService.hash_token("refresh-token")
    assert session.ip_address == "127.0.0.1"
    assert session.device_name == "Chrome on Windows"
    assert session.is_revoked is False
    assert session.expires_at > datetime.now(timezone.utc)


def test_refresh_session_is_expired_property():
    session = RefreshTokenService.create_session(
        token="refresh-token",
        user_uid=UserEntity().uid,
    )
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    assert session.is_expired is True
    assert session.is_valid is False


def test_jwt_service_creates_and_decodes_access_token(monkeypatch):
    from src.auth_service.external.security import jwt_service as module

    monkeypatch.setattr(
        module.settings.JWT_ACCESS_SECRET_KEY,
        "get_secret_value",
        lambda: "access-secret-for-tests-32-bytes-min"
    )
    monkeypatch.setattr(module.settings, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(module.settings, "JWT_ISSUER", "auth-service")
    monkeypatch.setattr(module.settings, "JWT_AUDIENCE", "auth-service-api")
    monkeypatch.setattr(module.settings, "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15)

    user = UserEntity(
        username="john",
        email="john@example.com",
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True,
    )

    service = JWTService()

    token = service.create_access_token(user)
    payload = service.decode_access_token(token)

    assert payload.sub == user.uid
    assert payload.role == UserRole.ADMIN.value
    assert payload.token_type == TokenType.ACCESS.value
    assert payload.jti is not None


def test_jwt_service_rejects_auth_token_as_access_token(monkeypatch):
    from src.auth_service.external.security import jwt_service as module

    monkeypatch.setattr(
        module.settings.JWT_ACCESS_SECRET_KEY,
        "get_secret_value",
        lambda: "access-secret-for-tests-32-bytes-min"
    )
    monkeypatch.setattr(
        module.settings.JWT_AUTH_SECRET_KEY,
        "get_secret_value",
        lambda: "auth-secret-for-tests-32-bytes-minimum"
    )
    monkeypatch.setattr(module.settings, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(module.settings, "JWT_ISSUER", "auth-service")
    monkeypatch.setattr(module.settings, "JWT_AUDIENCE", "auth-service-api")
    monkeypatch.setattr(module.settings, "JWT_AUTH_TOKEN_EXPIRE_MINUTES", 15)

    user = UserEntity(
        username="john",
        email="john@example.com",
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True,
    )

    service = JWTService()

    auth_token = service.create_auth_token(user)

    with pytest.raises(InvalidTokenError):
        service.decode_access_token(auth_token)


def test_jwt_service_creates_and_decodes_auth_token(monkeypatch):
    from src.auth_service.external.security import jwt_service as module

    monkeypatch.setattr(
        module.settings.JWT_AUTH_SECRET_KEY,
        "get_secret_value",
        lambda: "auth-secret-for-tests-32-bytes-minimum"
    )
    monkeypatch.setattr(module.settings, "JWT_ALGORITHM", "HS256")
    monkeypatch.setattr(module.settings, "JWT_ISSUER", "auth-service")
    monkeypatch.setattr(module.settings, "JWT_AUDIENCE", "auth-service-api")
    monkeypatch.setattr(module.settings, "JWT_AUTH_TOKEN_EXPIRE_MINUTES", 15)

    user = UserEntity(
        username="john",
        email="john@example.com",
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True,
    )

    service = JWTService()

    token = service.create_auth_token(user)
    payload = service.decode_auth_token(token)

    assert payload.sub == user.uid
    assert payload.role == UserRole.USER.value
    assert payload.token_type == TokenType.AUTH.value
    assert payload.jti is not None


def test_url_safe_token_service_creates_and_decodes_token(monkeypatch):
    from src.auth_service.core import security as module

    monkeypatch.setattr(
        module.settings.URL_SAFE_TOKEN_SECRET,
        "get_secret_value",
        lambda: "url-safe-secret",
    )

    service = URLSafeTokenService()

    token = service.create_token(
        data={"email": "john@example.com"},
        purpose=TokenPurpose.EMAIL_CONFIRMATION.value,
    )

    payload = service.decode_token(
        token=token,
        purpose=TokenPurpose.EMAIL_CONFIRMATION.value,
        max_age=60,
    )

    assert payload == {"email": "john@example.com"}


def test_url_safe_token_service_rejects_wrong_purpose(monkeypatch):
    from src.auth_service.core import security as module

    monkeypatch.setattr(
        module.settings.URL_SAFE_TOKEN_SECRET,
        "get_secret_value",
        lambda: "url-safe-secret",
    )

    service = URLSafeTokenService()

    token = service.create_token(
        data={"email": "john@example.com"},
        purpose=TokenPurpose.EMAIL_CONFIRMATION.value,
    )

    with pytest.raises(InvalidTokenError):
        service.decode_token(
            token=token,
            purpose=TokenPurpose.PASSWORD_RESET.value,
            max_age=60,
        )


def test_totp_service_encrypts_and_decrypts_secret(monkeypatch):
    from src.auth_service.external.security import totp_service as module

    key = Fernet.generate_key().decode()
    monkeypatch.setattr(
        module.settings.TOTP_ENCRYPTION_KEY,
        "get_secret_value",
        lambda: key,
    )
    monkeypatch.setattr(module.settings, "TOTP_ISSUER_NAME", "AuthService")
    monkeypatch.setattr(module.settings, "TOTP_VALID_WINDOW", 1)

    service = TOTPService()

    secret = service.generate_secret()
    encrypted = service.encrypt_secret(secret)
    decrypted = service.decrypt_secret(encrypted)

    assert encrypted != secret
    assert decrypted == secret


def test_totp_service_generates_uri_and_qr(monkeypatch):
    from src.auth_service.external.security import totp_service as module

    key = Fernet.generate_key().decode()
    monkeypatch.setattr(
        module.settings.TOTP_ENCRYPTION_KEY,
        "get_secret_value",
        lambda: key,
    )
    monkeypatch.setattr(module.settings, "TOTP_ISSUER_NAME", "AuthService")
    monkeypatch.setattr(module.settings, "TOTP_VALID_WINDOW", 1)

    service = TOTPService()

    secret = service.generate_secret()
    uri = service.generate_uri(secret, "john@example.com")
    qr = service.generate_qr_base64(uri)

    assert uri.startswith("otpauth://totp/")
    assert "john%40example.com" in uri or "john@example.com" in uri
    assert qr