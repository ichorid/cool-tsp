from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TSP_", env_file=".env", extra="ignore")

    max_nodes: int = Field(default=1000, ge=2, description="Max total nodes per request")
    default_solver: str = Field(default="2opt", description="Default solver strategy")
    log_level: str = Field(default="info", description="Logging level")
    two_opt_max_iterations: int = Field(
        default=100, ge=1, description="2-opt max iterations when selected"
    )


def get_settings() -> Settings:
    return Settings()
