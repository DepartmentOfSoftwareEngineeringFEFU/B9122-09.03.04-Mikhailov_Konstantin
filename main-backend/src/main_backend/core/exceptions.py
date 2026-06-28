class MainBackendError(Exception):

    def __init__(self, message: str = "Internal error", code: str = "INTERNAL_ERROR"):

        self.message = message

        self.code = code

        super().__init__(message)

class PredictionError(MainBackendError):

    def __init__(self, message: str = "Prediction failed"):

        super().__init__(message=message, code="PREDICTION_ERROR")

class PredictionNotFoundError(MainBackendError):

    def __init__(self, prediction_id: str):

        super().__init__(

            message=f"Prediction {prediction_id} not found",

            code="PREDICTION_NOT_FOUND",

        )

class ForecastingServiceUnavailable(MainBackendError):

    def __init__(self, details: str = ""):

        super().__init__(

            message=f"Forecasting service unavailable: {details}",

            code="FORECASTING_UNAVAILABLE",

        )

class AuthServiceUnavailable(MainBackendError):

    def __init__(self, details: str = ""):

        super().__init__(

            message=f"Auth service unavailable: {details}",

            code="AUTH_SERVICE_UNAVAILABLE",

        )

class UserNotFoundError(MainBackendError):

    def __init__(self, user_id: str):

        super().__init__(

            message=f"User {user_id} not found in auth-service",

            code="USER_NOT_FOUND",

        )

class UserDisabledError(MainBackendError):

    def __init__(self):

        super().__init__(

            message="User account is disabled",

            code="USER_DISABLED",

        )

class InvalidFeaturesError(MainBackendError):

    def __init__(self, details: str = ""):

        super().__init__(

            message=f"Invalid flat features: {details}",

            code="INVALID_FEATURES",

        )
