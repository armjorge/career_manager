from functools import lru_cache
from typing import Any

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    project: str = "career-app"
    cors_allow_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    db_schema: str = "consulting_tracker"

    db_postgresql: str = Field(default="", alias="DB_POSTGRESQL")
    documents_s3_bucket: str = Field(default="", alias="DOCUMENTS_S3_BUCKET")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    cognito_user_pool_id: str = Field(default="", alias="COGNITO_USER_POOL_ID")
    cognito_client_id: str = Field(default="", alias="COGNITO_CLIENT_ID")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @field_validator("db_postgresql", mode="before")
    @classmethod
    def strip_db_url(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().strip("'\"")


@lru_cache
def get_settings() -> Settings:
    return Settings()
