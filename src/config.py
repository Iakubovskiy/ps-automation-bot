"""Module for application configuration."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parents[1] / ".env.local"

class Settings(BaseSettings):
    """Bot settings and credentials."""
    bot_token: str
    gemini_api_key: str
    spreadsheet_id: str = ""
    google_service_account_file: str = "service_account.json"

    horoshop_store_url: str = "https://prostastal.com/edit/products/all"
    horoshop_email: str = os.getenv("HOROSHOP_EMAIL")
    horoshop_password: str = os.getenv("HOROSHOP_PASSWORD")
    playwright_headless: bool = True

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
