"""Module for asynchronous interaction with Google Sheets."""
import gspread_asyncio
from google.oauth2.service_account import Credentials
from src.config import settings

class GoogleSheetsService:
    """Service to handle Google Sheets operations."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.client_manager = gspread_asyncio.AsyncioGspreadClientManager
        (
            self._get_credentials
        )

    @staticmethod
    def _get_credentials() -> Credentials:
        """Get credentials from service account file."""
        creds = Credentials.from_service_account_file
        (
            settings.google_service_account_file
        )
        scoped_creds = creds.with_scopes
        (
            [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
            ]
        )
        return scoped_creds

    async def get_models(self) -> list[str]:
        """Fetch knife models from 'Items' sheet."""
        client = await self.client_manager.authorize()
        spreadsheet = await client.open_by_key(settings.spreadsheet_id)
        worksheet = await spreadsheet.worksheet("Items")
        # Отримуємо перший стовпчик (назви моделей)
        models = await worksheet.col_values(1)
        return models[1:]  # Пропускаємо заголовок

    async def append_item(self, row_data: list) -> None:
        """Append a new row to the 'Queue' sheet."""
        client = await self.client_manager.authorize()
        spreadsheet = await client.open_by_key(settings.spreadsheet_id)
        worksheet = await spreadsheet.worksheet("Queue")
        await worksheet.append_row(row_data)

# Створюємо екземпляр сервісу для використання в хендлерах
gs_service = GoogleSheetsService()