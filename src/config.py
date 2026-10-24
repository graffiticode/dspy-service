"""Configuration management for DSPy service."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Logging
    log_level: str = Field(default="info", description="Log level")

    # Service identification
    service_name: str = Field(default="dspy-service", description="Service name")
    service_version: str = Field(default="0.1.0", description="Service version")

    # Authentication
    internal_api_key: str = Field(default="", description="Internal API key for service-to-service auth")
    # Local development only. Without a key the service refuses every protected route, unless this is set:
    # a missing key must never open the service (it once did, silently, in production).
    allow_unauthenticated_dev: bool = Field(
        default=False, description="Serve protected routes without a key (local development only)"
    )

    class Config:
        env_prefix = ""
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
