from __future__ import annotations

import logging

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from main_backend.core.security import (

    CurrentUser,

    require_admin,

    verify_access_token,

)

from ...dependencies import get_auth_client

from ...integrations.auth_client import AuthClient, UserNotFoundError, AuthClientError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health"])

@router.get("/whoami")

async def whoami(

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

):

    return {

        "status": "ok",

        "source": "jwt_only",

        "user": {

            "sub": str(current_user.sub),

            "role": current_user.role,

            "jti": str(current_user.jti),

            "exp": current_user.exp.isoformat(),

            "iat": current_user.iat.isoformat(),

        },

    }

@router.get("/me")

async def get_current_user_profile(

    current_user: Annotated[CurrentUser, Depends(verify_access_token)],

    auth_client: Annotated[AuthClient, Depends(get_auth_client)],

):

    try:

        user_info = await auth_client.get_user(current_user.sub)

        if user_info is None:

            logger.error(

                f"User {current_user.sub} exists in JWT but not in auth-service. "

                f"Possible data inconsistency."

            )

            raise HTTPException(

                status_code=status.HTTP_404_NOT_FOUND,

                detail="User not found in auth-service",

            )

        if not user_info.is_active:

            logger.warning(f"User {current_user.sub} is disabled")

            raise HTTPException(

                status_code=status.HTTP_403_FORBIDDEN,

                detail="User account is disabled",

            )

        return {

            "status": "ok",

            "source": "jwt + auth-service",

            "user": {

                "uid": user_info.uid,

                "username": user_info.username,

                "email": user_info.email,

                "phone_number": user_info.phone_number,

                "role": user_info.role,

                "is_active": user_info.is_active,

                "is_email_verified": user_info.is_email_verified,

                "two_factor_enabled": user_info.two_factor_enabled,

                "created_at": user_info.created_at,

            },

            "jwt": {

                "jti": str(current_user.jti),

                "exp": current_user.exp.isoformat(),

                "iat": current_user.iat.isoformat(),

            },

        }

    except AuthClientError as e:

        logger.error(f"AuthClient error: {e}")

        raise HTTPException(

            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,

            detail=f"Failed to fetch user data: {str(e)}",

        )

    except Exception as e:

        logger.error(f"Unexpected error in /me: {e}", exc_info=True)

        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail="Internal server error",

        )

@router.get("/admin-only")

async def admin_only(

    current_user: Annotated[CurrentUser, Depends(require_admin)],

):

    return {

        "status": "ok",

        "message": f"Hello, admin {current_user.sub}!",

        "role": current_user.role,

    }
