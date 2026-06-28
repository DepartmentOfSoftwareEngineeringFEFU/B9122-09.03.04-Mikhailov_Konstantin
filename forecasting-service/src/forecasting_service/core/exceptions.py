"""
Domain exceptions for forecasting service.
"""
from typing import Any


class ForecastingError(Exception):
    """Base exception for forecasting service."""

    def __init__(self, message: str = "Forecasting error", code: str = "FORECASTING_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ModelNotFoundError(ForecastingError):
    """Model not found."""

    def __init__(self, model_version: str):
        super().__init__(
            message=f"Model '{model_version}' not found",
            code="MODEL_NOT_FOUND",
        )


class ModelNotLoadedError(ForecastingError):
    """Model not loaded."""

    def __init__(self):
        super().__init__(
            message="Model not loaded",
            code="MODEL_NOT_LOADED",
        )


class InvalidFeaturesError(ForecastingError):
    """Invalid features provided."""

    def __init__(self, message: str = "Invalid features"):
        super().__init__(message=message, code="INVALID_FEATURES")


class PredictionFailedError(ForecastingError):
    """Prediction failed."""

    def __init__(self, message: str = "Prediction failed"):
        super().__init__(message=message, code="PREDICTION_FAILED")