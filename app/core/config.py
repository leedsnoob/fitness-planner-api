from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Fitness Planner API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://tomchen@localhost:5432/fitness_planner"
    jwt_secret_key: str = "change-this-secret-to-at-least-32-characters"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    siliconflow_api_key: Optional[str] = None
    siliconflow_base_url: str = "https://api.siliconflow.cn/v1"
    siliconflow_model: str = "Qwen/Qwen3-8B"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
