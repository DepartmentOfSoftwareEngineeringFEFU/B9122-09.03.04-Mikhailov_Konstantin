from __future__ import annotations

import logging

from typing import Optional

from uuid import UUID

import httpx

from pydantic import BaseModel

from tenacity import (

    retry,

    retry_if_exception_type,

    stop_after_attempt,

    wait_exponential,

)

from main_backend.config import settings

logger = logging.getLogger(__name__)

class UserInfo(BaseModel):

    uid: str

    username: str

    email: str

    phone_number: Optional[str] = None

    role: str

    is_active: bool

    is_email_verified: bool

    two_factor_enabled: bool

    created_at: str

class AuthClientError(Exception):

    pass

class UserNotFoundError(AuthClientError):

    pass

class AuthClient:

    def __init__(self):

        self._base_url = settings.AUTH_SERVICE_URL.rstrip("/")

        self._internal_token = settings.INTERNAL_SERVICE_TOKEN

        self._timeout = settings.AUTH_CLIENT_TIMEOUT

    @retry(

        stop=stop_after_attempt(3),

        wait=wait_exponential(multiplier=1, min=1, max=5),

        retry=retry_if_exception_type(

            (httpx.TimeoutException, httpx.ConnectError)

        ),

        reraise=True,

    )

    async def get_user(self, user_id: UUID) -> Optional[UserInfo]:

        url = f"{self._base_url}/api/v1/internal/users/{user_id}"

        headers = {

            "X-Internal-Token": self._internal_token,

            "Accept": "application/json",

        }

        logger.debug(f"Fetching user {user_id} from auth-service")

        async with httpx.AsyncClient(timeout=self._timeout) as client:

            try:

                response = await client.get(url, headers=headers)

                if response.status_code == 404:

                    logger.warning(f"User {user_id} not found in auth-service")

                    return None

                if response.status_code == 401:

                    logger.error(

                        "Invalid INTERNAL_SERVICE_TOKEN. "

                        "Check that it matches in auth-service and main-backend."

                    )

                    raise AuthClientError("Internal authentication failed")

                response.raise_for_status()

                body = response.json()

                user_data = body.get("data")

                if not user_data:

                    logger.error(f"Empty user data for {user_id}")

                    return None

                return UserInfo.model_validate(user_data)

            except httpx.TimeoutException:

                logger.error(f"Timeout fetching user {user_id}")

                raise

            except httpx.ConnectError:

                logger.error(

                    f"Cannot connect to auth-service at {self._base_url}. "

                    f"Is auth-service running?"

                )

                raise

            except httpx.HTTPStatusError as e:

                logger.error(

                    f"HTTP error fetching user {user_id}: "

                    f"{e.response.status_code} {e.response.text}"

                )

                raise AuthClientError(

                    f"Auth-service returned {e.response.status_code}"

                )

            except AuthClientError:

                raise

            except Exception as e:

                logger.error(f"Unexpected error fetching user {user_id}: {e}")

                raise AuthClientError(f"Unexpected error: {e}")
