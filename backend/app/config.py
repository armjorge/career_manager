from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    db_postgresql: str = Field(alias="DB_POSTGRESQL")
    neon_auth_url: str | None = Field(default=None, alias="NEON_AUTH_URL")
    vite_neon_auth_url: str | None = Field(default=None, alias="VITE_NEON_AUTH_URL")
    api_prefix: str = "/api/v1"
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    api_gateway_base_path: str = Field(default="/", alias="API_GATEWAY_BASE_PATH")
    db_schema: str = "consulting_tracker"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", ROOT_DIR / "frontend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        raw = self.cors_origins_raw.strip()
        if raw.startswith("["):
            import json

            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                raise ValueError("CORS_ORIGINS JSON must be an array of strings")
            return [str(origin).strip() for origin in parsed if str(origin).strip()]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @field_validator("cors_origins_raw", mode="before")
    @classmethod
    def parse_cors_origins_raw(cls, value: Any) -> str:
        if isinstance(value, list):
            return ",".join(str(origin).strip() for origin in value if str(origin).strip())
        if value is None:
            return ""
        return str(value)

    @model_validator(mode="after")
    def normalize_settings(self) -> "Settings":
        if self.db_postgresql:
            self.db_postgresql = self.db_postgresql.strip().strip("'\"")
        if not self.neon_auth_url:
            self.neon_auth_url = self.vite_neon_auth_url
        if not self.neon_auth_url:
            raise ValueError("NEON_AUTH_URL or VITE_NEON_AUTH_URL must be set")
        if not self.api_gateway_base_path.startswith("/"):
            self.api_gateway_base_path = f"/{self.api_gateway_base_path}"
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
