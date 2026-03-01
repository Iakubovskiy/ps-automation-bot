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

    # ── Steel options ────────────────────────────────────────────────

    MOCK_STEELS: list[str] = ["Х12МФ", "D2", "95Х18", "Дамаск", "440С"]

    async def get_steel_options(self) -> list[str]:
        """Fetch available steel types from the 'Steels' worksheet."""
        if not self.available:
            logger.warning("Sheets unavailable — returning MOCK steels.")
            return list(self.MOCK_STEELS)

        try:
            client = await self.client_manager.authorize()
            spreadsheet = await client.open_by_key(settings.spreadsheet_id)
            worksheet = await spreadsheet.worksheet("Steels")
            values = await worksheet.col_values(1)
            return values[1:]
        except Exception as e:
            logger.error("Failed to fetch steels: %s", e)
            return list(self.MOCK_STEELS)

    # ── Handle-material options ──────────────────────────────────────

    MOCK_HANDLES: list[str] = ["Мікарта", "G10", "Паракорд", "Дерево", "Кістка"]

    async def get_handle_options(self) -> list[str]:
        """Fetch available handle materials from the 'Handles' worksheet."""
        if not self.available:
            logger.warning("Sheets unavailable — returning MOCK handles.")
            return list(self.MOCK_HANDLES)

        try:
            client = await self.client_manager.authorize()
            spreadsheet = await client.open_by_key(settings.spreadsheet_id)
            worksheet = await spreadsheet.worksheet("Handles")
            values = await worksheet.col_values(1)
            return values[1:]
        except Exception as e:
            logger.error("Failed to fetch handles: %s", e)
            return list(self.MOCK_HANDLES)

    # ── Blade specs lookup ───────────────────────────────────────────

    MOCK_BLADE_SPECS: dict = {
        "total_length": 280,
        "blade_length": 150,
        "blade_width": 35,
        "blade_weight": 180,
        "blade_thickness": 4.5,
        "hardness": 58,
        "sharpening_angle": 40,
        "configuration_type": None,
        "blade_type": "Ніж мисливський",
    }

    async def get_blade_specs(self, model_name: str) -> dict:
        """Look up blade specifications by model name in the worksheet."""
        if not self.available:
            logger.warning("Sheets unavailable — returning MOCK blade specs.")
            return dict(self.MOCK_BLADE_SPECS)

        try:
            client = await self.client_manager.authorize()
            spreadsheet = await client.open_by_key(settings.spreadsheet_id)

            worksheet = await spreadsheet.worksheet("Blades")
            all_rows = await worksheet.get_all_records()

            for row in all_rows:
                if row.get("Назва") == model_name:
                    raw_thickness = str(row.get("Товщина", "0")).replace(",", ".")

                    return {
                        "total_length": row.get("Загальна довжина", 0),
                        "blade_length": row.get("Довжина клинка", 0),
                        "blade_width": row.get("Ширина клинка", 0),
                        "blade_weight": row.get("Вага", 0),
                        "blade_thickness": float(raw_thickness),
                        "hardness": row.get("Твердість", 0),
                        "sharpening_angle": row.get("Кут заточки", 0),
                        "blade_type": row.get("Тип клинка", ""),
                    }

            logger.warning("Model '%s' not found in sheet.", model_name)
            return dict(self.MOCK_BLADE_SPECS)

        except Exception as e:
            logger.error("Failed to fetch blade specs: %s", e)
            return dict(self.MOCK_BLADE_SPECS)


gs_service = GoogleSheetsService()