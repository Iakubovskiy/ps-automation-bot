"""Horoshop distribution driver — manifest-driven Playwright automation.

Reads the DistributionManifest's JSON config to determine which fields to fill,
which selectors to use, and how to map product data to platform form fields.

This replaces the old hardcoded HoroshopIntegration with a configurable,
manifest-driven approach. The manifest_config JSON defines:
  - field_mapping: form field name → product data dotted path
  - spec_mapping: spec field name → product data dotted path
  - checkbox_mapping: checkbox labels → product data dotted path
  - seo_mapping: SEO field name → AI content dotted path
  - selectors: CSS selectors for the admin panel
"""
import logging
import re

import aiohttp
from playwright.async_api import Page

from modules.distribution.domain.distribution_manifest import DistributionManifest
from modules.distribution.infrastructure.playwright_browser import PlaywrightBrowser

logger = logging.getLogger(__name__)


class HoroshopDriver:
    """Playwright-based driver that publishes products to Horoshop.

    Reads DistributionManifest.manifest_config for all field mapping
    and selector configuration.
    """

    def __init__(self, browser: PlaywrightBrowser):
        self._browser = browser

    async def publish(
        self,
        manifest: DistributionManifest,
        product_data: dict,
    ) -> None:
        """Execute the full publish flow for a single product.

        Args:
            manifest: The manifest with JSON config and driver credentials.
            product_data: Combined dict with 'attributes' and 'ai_content' keys.
        """
        config = manifest.manifest_config
        credentials = manifest.driver.credentials
        selectors = config.get("selectors", {})

        page = await self._browser.get_page()

        try:
            await self._login(page, credentials)
            await self._navigate_to_new_product(page, selectors)
            await self._fill_mapped_fields(page, config, product_data, selectors)
            await self._fill_spec_fields(page, config, product_data, selectors)
            await self._fill_checkboxes(page, config, product_data, selectors)
            await self._fill_seo_fields(page, config, product_data, selectors)
            await self._upload_photos(page, product_data, selectors)
            await self._save(page, selectors)
            await self._add_video(page, product_data, selectors)

            manifest.mark_published()
            logger.info("Published product %s to Horoshop", manifest.product_id)

        except Exception as exc:
            manifest.mark_failed(str(exc))
            logger.exception("Failed to publish product %s", manifest.product_id)
            raise
        finally:
            await page.close()

    async def _login(self, page: Page, credentials: dict) -> None:
        """Log into the Horoshop admin panel."""
        url = credentials.get("store_url", "")
        await page.goto(url)
        await page.fill('input[type="text"]', credentials.get("email", ""))
        await page.fill('input[type="password"]', credentials.get("password", ""))
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)
        await page.wait_for_load_state("networkidle")
        logger.info("Logged into Horoshop")

    async def _navigate_to_new_product(self, page: Page, selectors: dict) -> None:
        """Navigate to the new product form."""
        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)
        await admin_frame.locator("#addGoodToCatalog").click()
        add_button = admin_frame.locator('a.button.add:has-text("Додати")')
        await add_button.click()
        await page.wait_for_load_state("networkidle")
        logger.info("Opened new product form")

    async def _fill_mapped_fields(
        self, page: Page, config: dict, product_data: dict, selectors: dict
    ) -> None:
        """Fill form fields using field_mapping from manifest config."""
        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        field_mapping = config.get("field_mapping", {})
        for selector_name, data_path in field_mapping.items():
            value = self._resolve_path(product_data, data_path)
            if value is None:
                continue

            selector = selectors.get(selector_name, f'input[name="{selector_name}"]')

            if selector.startswith("select"):
                await admin_frame.locator(selector).select_option(label=str(value))
            elif selector.endswith("_editor"):
                # CKEditor frame
                editor_frame = admin_frame.frame_locator(".cke_wysiwyg_frame").first
                await editor_frame.locator("body.cke_editable").fill(str(value))
            else:
                await admin_frame.locator(selector).fill(str(value))

        logger.info("Filled mapped fields")

    async def _fill_spec_fields(
        self, page: Page, config: dict, product_data: dict, selectors: dict
    ) -> None:
        """Fill specification input fields."""
        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        spec_mapping = config.get("spec_mapping", {})
        for field_name, data_path in spec_mapping.items():
            value = self._resolve_path(product_data, data_path)
            if value is None:
                continue

            selector = selectors.get(field_name, f'input[name="names[{field_name}]"]')

            if "select" in selector:
                await admin_frame.locator(selector).select_option(label=str(value))
            else:
                await admin_frame.locator(selector).fill(str(value))

        logger.info("Filled spec fields")

    async def _fill_checkboxes(
        self, page: Page, config: dict, product_data: dict, selectors: dict
    ) -> None:
        """Check/uncheck checkboxes based on checkbox_mapping."""
        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        checkbox_mapping = config.get("checkbox_mapping", {})
        for label_text, data_path in checkbox_mapping.items():
            value = self._resolve_path(product_data, data_path)
            if not value:
                continue

            if isinstance(value, list):
                for item in value:
                    label = admin_frame.locator("label").filter(has_text=item)
                    await label.locator('input[type="checkbox"]').check()
            elif isinstance(value, bool) and value:
                label = admin_frame.locator("label").filter(has_text=label_text)
                await label.locator('input[type="checkbox"]').check()
            elif isinstance(value, str):
                label = admin_frame.locator("label").filter(has_text=value)
                await label.locator('input[type="checkbox"]').check()

        logger.info("Filled checkboxes")

    async def _fill_seo_fields(
        self, page: Page, config: dict, product_data: dict, selectors: dict
    ) -> None:
        """Fill SEO-related fields from seo_mapping."""
        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        seo_mapping = config.get("seo_mapping", {})
        for field_name, data_path in seo_mapping.items():
            value = self._resolve_path(product_data, data_path)
            if value is None:
                continue

            selector = selectors.get(field_name, f'input[name="{field_name}"]')

            if "textarea" in selector:
                await admin_frame.locator(selector).fill(str(value))
            else:
                await admin_frame.locator(selector).fill(str(value))

        logger.info("Filled SEO fields")

    async def _upload_photos(
        self, page: Page, product_data: dict, selectors: dict
    ) -> None:
        """Upload product photos."""
        photos = product_data.get("attributes", {}).get("photos", [])
        if not photos:
            return

        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        add_button = admin_frame.locator('a:has-text("Додати зображення")').nth(1)
        await add_button.click()

        file_input = admin_frame.locator('input[type="file"]')
        await file_input.set_input_files(photos)

        logger.info("Uploaded %d photos", len(photos))

    async def _add_video(
        self, page: Page, product_data: dict, selectors: dict
    ) -> None:
        """Add YouTube video iframe if video_url is present."""
        video_url = product_data.get("attributes", {}).get("video_url", "")
        if not video_url:
            return

        video_html = await self._generate_youtube_iframe(video_url)
        if not video_html:
            return

        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        target_block = admin_frame.locator("li.modifications_imagepreview").last
        edit_button = target_block.locator('a[class="edit make-edit"]')
        await target_block.hover()
        await page.wait_for_timeout(300)
        await edit_button.click(force=True)
        await page.wait_for_timeout(300)

        textarea = target_block.locator('textarea[placeholder="код відео"]')
        await textarea.fill(video_html)
        await self._save(page, selectors)
        await page.wait_for_timeout(5000)

        logger.info("YouTube video injected")

    async def _save(self, page: Page, selectors: dict) -> None:
        """Click the save button."""
        frame_sel = selectors.get("admin_frame", 'iframe[src*="/adminLegacy/data.php"]')
        admin_frame = page.frame_locator(frame_sel)

        save_sel = selectors.get("save_button", 'a:has-text("Зберегти")')
        await admin_frame.locator(save_sel).first.click()
        await page.wait_for_load_state("networkidle")
        logger.info("Product saved")

    @staticmethod
    def _resolve_path(data: dict, path: str):
        """Resolve a dotted path from product data."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current

    @staticmethod
    async def _generate_youtube_iframe(url: str) -> str:
        """Extract video ID from URL and return HTML iframe."""
        match = re.search(r"(?:shorts/|v=|youtu\.be/)([0-9A-Za-z_-]{11})", url)
        if not match:
            return ""

        video_id = match.group(1)
        title = "YouTube Video"

        try:
            oembed_url = (
                f"https://www.youtube.com/oembed"
                f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
            )
            async with aiohttp.ClientSession() as session:
                async with session.get(oembed_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        title = data.get("title", title)
        except Exception:
            pass

        safe_title = title.replace('"', '&quot;')
        return (
            f'<iframe width="315" height="560" '
            f'src="https://www.youtube.com/embed/{video_id}" '
            f'title="{safe_title}" '
            f'frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; '
            f'gyroscope; picture-in-picture; web-share" '
            f'referrerpolicy="strict-origin-when-cross-origin" '
            f'allowfullscreen></iframe>'
        )
