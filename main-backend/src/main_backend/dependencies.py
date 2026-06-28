from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from .integrations.auth_client import AuthClient

def get_auth_client() -> AuthClient:

    return AuthClient()

AuthClientDep = Annotated[AuthClient, Depends(get_auth_client)]
