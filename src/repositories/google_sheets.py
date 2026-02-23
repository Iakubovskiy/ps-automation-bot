"""Module for asynchronous interaction with Google Sheets."""
import logging
from pathlib import Path

import gspread_asyncio
from google.oauth2.service_account import Credentials
from src.config import settings

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _is_sheets_configured() -> bool:
    """Check whether Google Sheets credentials are available."""
    if not settings.spreadsheet_id:
        return False

    sa_path = _PROJECT_ROOT / settings.google_service_account_file
    if not sa_path.exists():
        return False

    try:
        text = sa_path.read_text(encoding="utf-8")
        if '"client_email"' not in text:
            return False
    except Exception:
        return False

    return True


class GoogleSheetsService:
    """Service to handle Google Sheets operations."""

    MOCK_MODELS: list[str] = [
        "Ніж 'Козак'",
        "Ніж 'Вовк'",
        "Ніж 'Гайдамака'",
        "Ніж 'Сокіл'",
        "Ніж 'Кабан'",
    ]

    def __init__(self) -> None:
        """Initialize the service."""
        self.available = _is_sheets_configured()
        self.client_manager = None

        if self.available:
            self.client_manager = gspread_asyncio.AsyncioGspreadClientManager(
                self._get_credentials
            )
            logger.info("Google Sheets integration enabled.")
        else:
            logger.warning(
                "Google Sheets integration DISABLED — "
                "service_account JSON missing or invalid. "
                "Bot will run with stub data."
            )
        logger.info("Spreadsheet integration enabled.")

    @staticmethod
    def _get_credentials() -> Credentials:
        """Get credentials from service account file."""
        creds = Credentials.from_service_account_file(
            str(_PROJECT_ROOT / settings.google_service_account_file)
        )
        scoped_creds = creds.with_scopes(
            [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
        )
        return scoped_creds

    async def get_models(self) -> list[str]:
        """Fetch knife models from Items sheet."""
        if not self.available:
            logger.warning("Sheets unavailable — returning MOCK models.")
            return list(self.MOCK_MODELS)

        try:
            client = await self.client_manager.authorize()
            spreadsheet = await client.open_by_key(settings.spreadsheet_id)
            worksheet = await spreadsheet.worksheet("Blades")
            models = await worksheet.col_values(1)

            return models[1:]

        except Exception as e:
            logger.error(f"Failed to fetch models from Google Sheets: {e}")
            logger.info("Falling back to MOCK models to prevent bot crash.")
            return list(self.MOCK_MODELS)

gs_service = GoogleSheetsService()