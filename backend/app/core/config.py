"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://mosquisense:mosquisense@localhost:5432/mosquisense"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000"]
    mlflow_tracking_uri: str = "http://localhost:5000"
    mosdac_username: str = ""
    mosdac_password: str = ""
    mosdac_bounding_box: str = "26.7,26.95,80.8,81.1"
    weather_api_key: str = ""
    lucknow_center_lat: float = 26.8467
    lucknow_center_lon: float = 80.9462

    # Ensemble weights (Module 7)
    ensemble_weight_catboost: float = 0.40
    ensemble_weight_tft: float = 0.35
    ensemble_weight_ndwi: float = 0.25


settings = Settings()
