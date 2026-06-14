from __future__ import annotations

import logging

from dataclasses import dataclass

from datetime import datetime, timezone

from typing import Annotated, Callable

from uuid import UUID

from fastapi import Depends, HTTPException, status

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt

from main_backend.config import settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=True)

@dataclass(frozen=True)

class CurrentUser:

    sub: UUID                     

    role: str                                          

    jti: UUID                                                 

    exp: datetime                   

    iat: datetime                  

    token_type: str                      

async def verify_access_token(

    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],

) -> CurrentUser:

    token = credentials.credentials

    try:

        payload = jwt.decode(

            token,

            settings.JWT_ACCESS_SECRET_KEY.get_secret_value(),

            algorithms=[settings.JWT_ALGORITHM],

            issuer=settings.JWT_ISSUER,

            audience=settings.JWT_AUDIENCE,

            options={

                "verify_exp": True,

                "verify_iss": True,

                "verify_aud": True,

                "require": ["sub", "exp", "iat", "iss", "aud", "jti", "type", "role"],

            },

        )

        token_type = payload.get("type")

        if token_type != "access":

            logger.warning(f"Invalid token type: {token_type}")

            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail="Invalid token type. Expected access token.",

                headers={"WWW-Authenticate": "Bearer"},

            )

        try:

            sub = UUID(payload["sub"])

            jti = UUID(payload["jti"])

        except (ValueError, KeyError) as e:

            logger.warning(f"Invalid UUID in token: {e}")

            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail="Invalid token payload",

                headers={"WWW-Authenticate": "Bearer"},

            )

        role = payload.get("role")

        if not role or not isinstance(role, str):

            raise HTTPException(

                status_code=status.HTTP_401_UNAUTHORIZED,

                detail="Invalid role in token",

                headers={"WWW-Authenticate": "Bearer"},

            )

        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)

        return CurrentUser(

            sub=sub,

            role=role,

            jti=jti,

            exp=exp,

            iat=iat,

            token_type=token_type,

        )

    except jwt.ExpiredSignatureError:

        logger.info("Token expired")

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Token has expired. Please login again.",

            headers={"WWW-Authenticate": "Bearer"},

        )

    except jwt.JWTClaimsError as e:

        logger.warning(f"JWT claims error: {e}")

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail=f"Invalid token claims: {e}",

            headers={"WWW-Authenticate": "Bearer"},

        )

    except JWTError as e:

        logger.warning(f"JWT validation failed: {e}")

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="Invalid or malformed token",

            headers={"WWW-Authenticate": "Bearer"},

        )

def require_roles(*allowed_roles: str) -> Callable:

    async def _check_role(

        current_user: Annotated[CurrentUser, Depends(verify_access_token)],

    ) -> CurrentUser:

        if current_user.role not in allowed_roles:

            logger.warning(

                f"Access denied for user {current_user.sub}: "

                f"role={current_user.role}, required={allowed_roles}"

            )

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail=f"Access denied. Required role: {', '.join(allowed_roles)}",

            )

        return current_user

    return _check_role

require_user = require_roles("USER", "MODERATOR", "ADMIN", "OWNER")

require_moderator = require_roles("MODERATOR", "ADMIN", "OWNER")

require_admin = require_roles("ADMIN", "OWNER")

require_owner = require_roles("OWNER")

async def get_current_user_id(

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

) -> UUID:

    return current_user.sub
