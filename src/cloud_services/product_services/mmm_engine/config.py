"""
Configuration models for MMM Engine.
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class MMMSettings(BaseSettings):
    """Service-level configuration."""

    service_name: str = Field(default="MMM Engine")
    service_version: str = Field(default="0.1.0")
    cors_allow_origins: list[str] = Field(default=["*"])
    observability_mode: str = Field(default="prometheus")

    class Config:
        env_prefix = "MMM_"
        case_sensitive = False


settings = MMMSettings()


