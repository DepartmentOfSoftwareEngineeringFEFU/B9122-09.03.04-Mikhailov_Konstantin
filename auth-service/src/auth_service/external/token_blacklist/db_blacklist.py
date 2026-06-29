import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession


from src.auth_service.external.database.models import (
    TokenBlacklistModel,
    UserTokenRevocationModel,
)

logger = logging.getLogger(__name__)


class DatabaseTokenBlacklist:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def blacklist_token(
        self, jti: str, user_uid: str, expires_at: datetime,
    ) -> None:
        stmt = pg_insert(TokenBlacklistModel).values(
            jti=jti,
            user_uid=user_uid,
            expires_at=expires_at,
        ).on_conflict_do_nothing(index_elements=["jti"])

        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(
            {
                "event": "token_blacklisted",
                "jti": jti,
            }
        )

    async def is_blacklisted(self, jti: str) -> bool:
        stmt = select(
            TokenBlacklistModel.id
        ).where(
            TokenBlacklistModel.jti == jti
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def blacklist_all_for_user(
        self, user_uid: str, before: datetime,
    ) -> None:
        stmt = pg_insert(UserTokenRevocationModel).values(
            user_uid=user_uid,
            revoked_before=before,
        ).on_conflict_do_update(
            index_elements=["user_uid"],
            set_={"revoked_before": before},
        )

        await self._session.execute(stmt)
        await self._session.flush()

        logger.info(
            {
                "event": "all_user_tokens_revoked",
                "user_uid": user_uid,
            }
        )

    async def is_user_tokens_revoked(
        self, user_uid: str, issued_at: datetime,
    ) -> bool:
        stmt = select(
            UserTokenRevocationModel.revoked_before
        ).where(
            UserTokenRevocationModel.user_uid == user_uid
        )
        result = await self._session.execute(stmt)
        revoked_before = result.scalar_one_or_none()

        if revoked_before is None:
            return False

        return issued_at < revoked_before

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        stmt = delete(TokenBlacklistModel).where(
            TokenBlacklistModel.expires_at < now
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        deleted = result.rowcount
        if deleted:
            logger.info(
                {
                    "event": "expired_tokens_cleaned",
                    "deleted_count": deleted,
                }
            )
        return deleted