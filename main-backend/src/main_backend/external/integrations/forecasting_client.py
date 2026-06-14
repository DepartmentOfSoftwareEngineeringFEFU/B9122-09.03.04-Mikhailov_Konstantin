from __future__ import annotations

import logging

from dataclasses import dataclass

import httpx

from tenacity import (

    retry,

    retry_if_exception_type,

    stop_after_attempt,

    wait_exponential,

)

from ...config import settings

from ...core.exceptions import ForecastingServiceUnavailable

logger = logging.getLogger(__name__)

@dataclass

class ForecastingResult:

    predicted_price: float

    predicted_price_per_sqm: float

    confidence: float

    model_version: str

class ForecastingClient:

    def __init__(self):

        self._base_url = settings.FORECASTING_SERVICE_URL.rstrip("/")

        self._timeout = settings.FORECASTING_CLIENT_TIMEOUT

    async def health_check(self) -> bool:

        try:

            async with httpx.AsyncClient(timeout=3.0) as client:

                response = await client.get(f"{self._base_url}/health")

                if response.status_code == 200:

                    data = response.json()

                    return data.get("data", {}).get("model_loaded", False)

            return False

        except Exception:

            return False

    @retry(

        stop=stop_after_attempt(3),

        wait=wait_exponential(multiplier=1, min=1, max=5),

        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),

        reraise=True,

    )

    async def predict(self, features: dict, horizon: str = "now") -> ForecastingResult:

        url = f"{self._base_url}/api/v1/predictions/"

        payload = {"features": features, "horizon": horizon}

        try:

            async with httpx.AsyncClient(timeout=self._timeout) as client:

                response = await client.post(url, json=payload)

                response.raise_for_status()

                body = response.json()

                return ForecastingResult(

                    predicted_price=float(body["predicted_price"]),

                    predicted_price_per_sqm=float(body["predicted_price_per_sqm"]),

                    confidence=float(body.get("confidence", 0.85)),

                    model_version=body.get("model_version", "unknown"),

                )

        except httpx.ConnectError as e:

            logger.error(f"Cannot connect to forecasting-service: {e}")

            raise ForecastingServiceUnavailable(str(e))

        except httpx.TimeoutException as e:

            logger.error(f"Timeout calling forecasting-service: {e}")

            raise ForecastingServiceUnavailable("timeout")

        except httpx.HTTPStatusError as e:

            logger.error(f"Forecasting-service HTTP error: {e.response.status_code}")

            raise ForecastingServiceUnavailable(f"HTTP {e.response.status_code}")

        except Exception as e:

            logger.error(f"Unexpected error: {e}")

            raise ForecastingServiceUnavailable(str(e))
