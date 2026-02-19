"""Module for application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Bot settings and credentials."""
    bot_token: str
    spreadsheet_id: str
    google_service_account_file: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
