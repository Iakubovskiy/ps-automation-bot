"""Module for asynchronous interaction with Google Sheets."""
import gspread_asyncio
from google.oauth2.service_account import Credentials
from src.config import settings 

class GoogleSheetsService:
    """Service to handle Google Sheets operations."""
    def __init__(self):
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(self._get_credentials)

    @staticmethod
    def _get_credentials() -> Credentials: