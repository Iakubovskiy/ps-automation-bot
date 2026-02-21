"""Module for application configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to the project root (one level above src/).
# In Docker the file won't exist — Pydantic will still read OS env vars.
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

class Settings(BaseSettings):
    """Bot settings and credentials."""
    bot_token: str
    spreadsheet_id: str = ""
    google_service_account_file: str = "service_account.json"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
    )

settings = Settings()
