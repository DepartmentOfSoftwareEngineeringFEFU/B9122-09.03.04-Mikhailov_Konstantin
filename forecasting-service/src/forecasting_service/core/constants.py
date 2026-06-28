"""
Constants for forecasting service.
"""
from enum import Enum


class ForecastHorizon(str, Enum):
    """Forecast horizons."""

    NOW = "now"
    SIX_MONTHS = "6_months"
    ONE_YEAR = "1_year"


class ModelStatus(str, Enum):
    """Model status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRAINING = "training"
    FAILED = "failed"


# Market trends (multipliers)
MARKET_TRENDS = {
    ForecastHorizon.NOW: {"multiplier": 1.0, "confidence_delta": 0.0},
    ForecastHorizon.SIX_MONTHS: {"multiplier": 1.032, "confidence_delta": -0.05},
    ForecastHorizon.ONE_YEAR: {"multiplier": 1.068, "confidence_delta": -0.13},
}