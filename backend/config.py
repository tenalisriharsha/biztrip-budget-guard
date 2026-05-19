"""
Configuration module for BizTrip Budget Guard.
Loads settings from environment variables with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "BizTrip Budget Guard"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./biztrip.db"

    # API Keys
    groq_api_key: str = ""
    amadeus_api_key: str = ""
    amadeus_api_secret: str = ""
    tequila_api_key: str = ""
    exchange_rate_api_key: str = ""

    # Feature Flags & Fallbacks
    enable_groq: bool = True
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "mixtral-8x7b-32768"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
