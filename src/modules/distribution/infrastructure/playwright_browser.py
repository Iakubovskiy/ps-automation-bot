"""Shared Playwright browser lifecycle manager.

Provides a single browser instance reused across distribution drivers.
Handles launch, page creation, and cleanup.
"""
import logging

from playwright.async_api import async_playwright, Browser, Page, Playwright

logger = logging.getLogger(__name__)


class PlaywrightBrowser:
    """Manages a shared Playwright browser instance for distribution drivers."""

    def __init__(self, headless: bool = True):
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def get_page(self) -> Page:
        """Return a new page, launching browser if needed."""
        if not self._browser or not self._browser.is_connected():
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless
            )
            logger.info("Playwright browser launched (headless=%s)", self._headless)

        page = await self._browser.new_page()
        return page

    async def close(self) -> None:
        """Shut down the browser and Playwright instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Playwright browser closed")
