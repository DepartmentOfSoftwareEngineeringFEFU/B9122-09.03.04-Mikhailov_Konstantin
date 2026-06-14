from enum import Enum

class UserRole(str, Enum):

    USER = "USER"

    MODERATOR = "MODERATOR"

    ADMIN = "ADMIN"

    OWNER = "OWNER"

class ForecastHorizon(str, Enum):

    NOW = "now"

    SIX_MONTHS = "6_months"

    ONE_YEAR = "1_year"

class PredictionStatus(str, Enum):

    PENDING = "pending"

    SUCCESS = "success"

    FAILED = "failed"

MARKET_TRENDS = {

    ForecastHorizon.NOW: {"multiplier": 1.0, "confidence_delta": 0.0},

    ForecastHorizon.SIX_MONTHS: {"multiplier": 1.032, "confidence_delta": -0.05},

    ForecastHorizon.ONE_YEAR: {"multiplier": 1.068, "confidence_delta": -0.13},

}
