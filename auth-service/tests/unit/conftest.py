from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from src.auth_service.core.constants import UserRole
from src.auth_service.domain.entities import (
    RefreshSession,
    TokenPayload,
    UserEntity,
)
from src.auth_service.external.security.refresh_token_service import (
    RefreshTokenService,
)


class FakeUserRepository:
    def __init__(self):
        self.users: dict[UUID, UserEntity] = {}

    async def get_by_id(self, uid: UUID) -> UserEntity | None:
        return self.users.get(uid)

    async def get_by_email(self, email: str) -> UserEntity | None:
        normalized = email.lower().strip()
        return next(
            (u for u in self.users.values() if u.email == normalized),
            None,
        )

    async def get_by_username(self, username: str) -> UserEntity | None:
        normalized = username.strip()
        return next(
            (u for u in self.users.values() if u.username == normalized),
            None,
        )

    async def get_by_phone(self, phone: str) -> UserEntity | None:
        return next(
            (u for u in self.users.values() if u.phone_number == phone),
            None,
        )

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[UserEntity]:
        users = sorted(
            self.users.values(),
            key=lambda u: u.created_at,
            reverse=True,
        )
        return users[offset : offset + limit]

    async def count(self) -> int:
        return len(self.users)

    async def create(self, user: UserEntity) -> UserEntity:
        self.users[user.uid] = user
        return user

    async def update(self, user: UserEntity) -> UserEntity:
        if user.uid not in self.users:
            raise ValueError(f"User {user.uid} not found")
        self.users[user.uid] = user
        return user

    async def delete(self, uid: UUID) -> None:
        self.users.pop(uid, None)

    async def exists_by_email(self, email: str) -> bool:
        return await self.get_by_email(email) is not None

    async def exists_by_username(self, username: str) -> bool:
        return await self.get_by_username(username) is not None

    async def exists_by_phone(self, phone: str) -> bool:
        return await self.get_by_phone(phone) is not None


class FakeRefreshSessionRepository:
    def __init__(self):
        self.sessions: dict[str, RefreshSession] = {}

    async def create(
        self,
        session: RefreshSession,
    ) -> RefreshSession:
        if session.id is None:
            session.id = len(self.sessions) + 1
        self.sessions[session.token_hash] = session
        return session

    async def get_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshSession | None:
        return self.sessions.get(token_hash)

    async def revoke(self, token_hash: str) -> None:
        session = self.sessions.get(token_hash)
        if session:
            session.is_revoked = True

    async def revoke_all_for_user(self, user_uid: UUID) -> int:
        count = 0
        for session in self.sessions.values():
            if session.user_uid == user_uid and not session.is_revoked:
                session.is_revoked = True
                count += 1
        return count

    async def get_active_sessions(
        self,
        user_uid: UUID,
    ) -> list[RefreshSession]:
        sessions = [
            s
            for s in self.sessions.values()
            if s.user_uid == user_uid
            and not s.is_revoked
            and not s.is_expired
        ]
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    async def count_active_sessions(self, user_uid: UUID) -> int:
        return len(await self.get_active_sessions(user_uid))

    async def mark_replaced(
        self,
        old_token_hash: str,
        new_token_hash: str,
    ) -> None:
        session = self.sessions.get(old_token_hash)
        if session:
            session.is_revoked = True
            session.replaced_by = new_token_hash

    async def update_last_used(self, token_hash: str) -> None:
        session = self.sessions.get(token_hash)
        if session:
            session.last_used_at = datetime.now(timezone.utc)

    async def cleanup_expired(self) -> int:
        expired = [
            token_hash
            for token_hash, session in self.sessions.items()
            if session.is_expired
        ]
        for token_hash in expired:
            del self.sessions[token_hash]
        return len(expired)


class FakeAuditLog:
    def __init__(self):
        self.entries: list[dict] = []

    async def log(
        self,
        action: str,
        actor_uid: UUID | None = None,
        target_uid: UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        success: bool = True,
    ) -> None:
        self.entries.append(
            {
                "action": action,
                "actor_uid": actor_uid,
                "target_uid": target_uid,
                "details": details,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "request_id": request_id,
                "success": success,
            }
        )

    async def get_user_history(
        self,
        user_uid: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        items = [
            e
            for e in self.entries
            if e["actor_uid"] == user_uid or e["target_uid"] == user_uid
        ]
        return items[offset : offset + limit]

    async def get_by_action(
        self,
        action: str,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        items = [e for e in self.entries if e["action"] == action]
        return items[offset : offset + limit]

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        return self.entries[offset : offset + limit]


class FakeTokenBlacklist:
    def __init__(self):
        self.blacklisted_jti: set[str] = set()
        self.user_revocations: dict[UUID, datetime] = {}

    async def blacklist_token(
        self,
        jti: str,
        user_uid: UUID,
        expires_at: datetime,
    ) -> None:
        self.blacklisted_jti.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        return jti in self.blacklisted_jti

    async def are_blacklisted(self, jti_list: list[str]) -> list[str]:
        return [jti for jti in jti_list if jti in self.blacklisted_jti]

    async def blacklist_all_for_user(
        self,
        user_uid: UUID,
        before: datetime,
    ) -> None:
        self.user_revocations[user_uid] = before

    async def is_user_tokens_revoked(
        self,
        user_uid: UUID,
        issued_at: datetime,
    ) -> bool:
        revoked_before = self.user_revocations.get(user_uid)
        if revoked_before is None:
            return False

        if issued_at.tzinfo is None:
            issued_at = issued_at.replace(tzinfo=timezone.utc)

        if revoked_before.tzinfo is None:
            revoked_before = revoked_before.replace(tzinfo=timezone.utc)

        return issued_at <= revoked_before

    async def cleanup_expired(self) -> int:
        return 0


class FakeUnitOfWork:
    def __init__(self):
        self.users = FakeUserRepository()
        self.refresh_sessions = FakeRefreshSessionRepository()
        self.audit = FakeAuditLog()
        self.token_blacklist = FakeTokenBlacklist()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class FakePasswordHasher:
    def __init__(self):
        self.needs_rehash_result = False

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, hash: str) -> bool:
        return hash == f"hashed:{password}"

    def needs_rehash(self, hash: str) -> bool:
        return self.needs_rehash_result


class FakeTokenService:
    def __init__(self):
        self.auth_payloads: dict[str, TokenPayload] = {}
        self.access_payloads: dict[str, TokenPayload] = {}

    def create_access_token(self, user: UserEntity) -> str:
        token = f"access:{user.uid}"
        payload = TokenPayload(
            sub=user.uid,
            role=user.role.value,
            token_type="access",
            exp=datetime.now(timezone.utc) + timedelta(minutes=15),
            iat=datetime.now(timezone.utc),
            iss="auth-service",
            aud="auth-service-api",
            jti=uuid4(),
        )
        self.access_payloads[token] = payload
        return token

    def decode_access_token(self, token: str) -> TokenPayload:
        return self.access_payloads[token]

    def create_auth_token(self, user: UserEntity) -> str:
        token = f"auth:{user.uid}"
        payload = TokenPayload(
            sub=user.uid,
            role=user.role.value,
            token_type="auth",
            exp=datetime.now(timezone.utc) + timedelta(minutes=15),
            iat=datetime.now(timezone.utc),
            iss="auth-service",
            aud="auth-service-api",
            jti=uuid4(),
        )
        self.auth_payloads[token] = payload
        return token

    def decode_auth_token(self, token: str) -> TokenPayload:
        return self.auth_payloads[token]


class FakeURLTokenService:
    def __init__(self):
        self.tokens: dict[str, dict] = {}

    def create_token(self, data: dict, purpose: str) -> str:
        token = f"url-token:{purpose}:{len(self.tokens) + 1}"
        self.tokens[token] = {"data": data, "purpose": purpose}
        return token

    def decode_token(
        self,
        token: str,
        purpose: str,
        max_age: int,
    ) -> dict:
        stored = self.tokens[token]
        assert stored["purpose"] == purpose
        return stored["data"]


class FakeTOTPService:
    def __init__(self):
        self.valid_code = "123456"

    def generate_secret(self) -> str:
        return "TOTPSECRET"

    def encrypt_secret(self, secret: str) -> str:
        return f"encrypted:{secret}"

    def decrypt_secret(self, encrypted: str) -> str:
        return encrypted.removeprefix("encrypted:")

    def generate_uri(self, secret: str, email: str) -> str:
        return f"otpauth://totp/{email}?secret={secret}"

    def generate_qr_base64(self, uri: str) -> str:
        return "base64-qr"

    def verify_code(self, secret: str, code: str) -> bool:
        return code == self.valid_code


class FakeEmailService:
    def __init__(self):
        self.confirmation_emails: list[dict] = []
        self.password_reset_emails: list[dict] = []

    async def send_confirmation_email(
        self,
        email: str,
        username: str,
        token: str,
    ) -> None:
        self.confirmation_emails.append(
            {
                "email": email,
                "username": username,
                "token": token,
            }
        )

    async def send_password_reset_email(
        self,
        email: str,
        username: str,
        token: str,
    ) -> None:
        self.password_reset_emails.append(
            {
                "email": email,
                "username": username,
                "token": token,
            }
        )


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()


@pytest.fixture
def url_token_service() -> FakeURLTokenService:
    return FakeURLTokenService()


@pytest.fixture
def totp_service() -> FakeTOTPService:
    return FakeTOTPService()


@pytest.fixture
def email_service() -> FakeEmailService:
    return FakeEmailService()


@pytest.fixture
def auth_service(
    uow,
    hasher,
    token_service,
    url_token_service,
    totp_service,
    email_service,
):
    from src.auth_service.app.auth.service import AuthService

    return AuthService(
        uow=uow,
        hasher=hasher,
        token_service=token_service,
        url_token_service=url_token_service,
        totp_service=totp_service,
        email_service=email_service,
    )


@pytest.fixture
def active_user(hasher) -> UserEntity:
    return UserEntity(
        uid=uuid4(),
        username="john",
        email="john@example.com",
        password_hash=hasher.hash("SecurePass1!"),
        phone_number="+79001234567",
        role=UserRole.USER,
        is_active=True,
        is_email_verified=True,
    )


@pytest.fixture
def inactive_user(hasher) -> UserEntity:
    return UserEntity(
        uid=uuid4(),
        username="blocked",
        email="blocked@example.com",
        password_hash=hasher.hash("SecurePass1!"),
        role=UserRole.USER,
        is_active=False,
        is_email_verified=True,
    )


@pytest.fixture
def access_payload(active_user) -> TokenPayload:
    now = datetime.now(timezone.utc)
    return TokenPayload(
        sub=active_user.uid,
        role=active_user.role.value,
        token_type="access",
        exp=now + timedelta(minutes=15),
        iat=now,
        iss="auth-service",
        aud="auth-service-api",
        jti=uuid4(),
    )


@pytest.fixture
def profile_service(
    uow,
    hasher,
    totp_service,
):
    from src.auth_service.app.profile.service import ProfileService

    return ProfileService(
        uow=uow,
        hasher=hasher,
        totp_service=totp_service,
    )


@pytest.fixture
def admin_service(uow):
    from src.auth_service.app.admin.service import AdminService

    return AdminService(uow=uow)


@pytest.fixture
def admin_user(hasher) -> UserEntity:
    return UserEntity(
        uid=uuid4(),
        username="admin",
        email="admin@example.com",
        password_hash=hasher.hash("SecurePass1!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_email_verified=True,
    )


@pytest.fixture
def owner_user(hasher) -> UserEntity:
    return UserEntity(
        uid=uuid4(),
        username="owner",
        email="owner@example.com",
        password_hash=hasher.hash("SecurePass1!"),
        role=UserRole.OWNER,
        is_active=True,
        is_email_verified=True,
    )