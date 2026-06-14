from pathlib import Path

from functools import lru_cache

from pydantic import Field, SecretStr, PostgresDsn, RedisDsn

from pydantic_settings import BaseSettings, SettingsConfigDict

from enum import Enum

class Environment(str, Enum):

    DEVELOPMENT = "development"

    STAGING = "staging"

    PRODUCTION = "production"

    TESTING = "testing"

class Settings(BaseSettings):

    model_config = SettingsConfigDict(

        env_file=".env",

        env_file_encoding="utf-8",

        case_sensitive=True,

        extra="ignore",

    )

    APP_NAME: str = "real-estate-app"

    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    DEBUG: bool = False

    POSTGRES_USER: str

    POSTGRES_PASSWORD: SecretStr

    POSTGRES_HOST: str

    POSTGRES_PORT: str

    POSTGRES_DB: str

    @property

    def db_url(self) -> str:

        password = self.POSTGRES_PASSWORD.get_secret_value()

        return (

            f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}"

            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"

            f"/{self.POSTGRES_DB}"

        )

    JWT_ALGORITHM: str = "HS256"

    JWT_ACCESS_SECRET_KEY: SecretStr

    JWT_ISSUER: str = "auth-service"

    JWT_AUDIENCE: str = "real-estate-app"

    INTERNAL_SERVICE_TOKEN: str

    AUTH_SERVICE_URL: str = "http://localhost:8001"

    FORECASTING_SERVICE_URL: str = "http://localhost:8003"

    AUTH_CLIENT_TIMEOUT: float = 5.0

    FORECASTING_CLIENT_TIMEOUT: float = 30.0

    REDIS_URL: RedisDsn = RedisDsn("redis://localhost:6379/0")

    USER_CACHE_TTL: int = 300 

    CORS_ORIGINS: list[str] = [

        "http://localhost:5173", 

        "http://localhost:3000",

    ]

    CORS_ALLOW_CREDENTIALS: bool = True

    PREDICTION_RATE_LIMIT: int = 20                      

    PREDICTION_RATE_WINDOW: int = 3600         

@lru_cache

def get_settings() -> Settings:

    return Settings()

settings = get_settings()
