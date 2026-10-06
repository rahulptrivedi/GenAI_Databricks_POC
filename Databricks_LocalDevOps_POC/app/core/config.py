"""Validated application settings."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed configuration with safe local defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = Field(default="dev", alias="ENVIRONMENT", min_length=1)
    databricks_host: str | None = Field(default=None, alias="DATABRICKS_HOST")
    databricks_client_id: str | None = Field(default=None, alias="DATABRICKS_CLIENT_ID")
    databricks_client_secret: SecretStr | None = Field(
        default=None, alias="DATABRICKS_CLIENT_SECRET"
    )
    warehouse_id: str | None = Field(default=None, alias="DATABRICKS_WAREHOUSE_ID")
    genie_agent_id: str | None = Field(default=None, alias="DATABRICKS_GENIE_AGENT_ID")
    catalog: str = Field(default="chatbot_demo", alias="DATABRICKS_CATALOG", min_length=1)
    schema_name: str = Field(default="gold", alias="DATABRICKS_SCHEMA", min_length=1)
    app_name: str | None = Field(default=None, alias="DATABRICKS_APP_NAME")
    mlflow_experiment_name: str | None = Field(default=None, alias="MLFLOW_EXPERIMENT_NAME")
    question_max_chars: int = Field(default=2000, alias="QUESTION_MAX_CHARS", ge=1, le=10000)
    genie_timeout_seconds: int = Field(default=60, alias="GENIE_TIMEOUT_SECONDS", ge=1, le=600)
    genie_http_timeout_seconds: int = Field(
        default=15, alias="GENIE_HTTP_TIMEOUT_SECONDS", ge=1, le=120
    )
    genie_poll_interval_seconds: float = Field(
        default=1.0, alias="GENIE_POLL_INTERVAL_SECONDS", gt=0, le=30
    )

    @property
    def genie_configured(self) -> bool:
        """Return whether a Genie resource has been selected."""
        return self.genie_agent_id is not None and bool(self.genie_agent_id.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for the current process."""
    return Settings()
