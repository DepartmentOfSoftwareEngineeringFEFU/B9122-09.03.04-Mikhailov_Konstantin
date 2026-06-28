from datetime import datetime, timezone

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):

    status: str = "ok"

    data: Optional[T] = None

    meta: Optional[dict] = None

    timestamp: str

    def __init__(self, **data):

        if "timestamp" not in data:

            data["timestamp"] = datetime.now(timezone.utc).isoformat()

        super().__init__(**data)

class ErrorDetail(BaseModel):

    code: str

    message: str

    details: Optional[dict] = None

class ErrorResponse(BaseModel):

    status: str = "error"

    error: ErrorDetail

    timestamp: str

    def __init__(self, **data):

        if "timestamp" not in data:

            data["timestamp"] = datetime.now(timezone.utc).isoformat()

        super().__init__(**data)
