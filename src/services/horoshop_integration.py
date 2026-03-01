"""Хорошоп platform integration using Playwright."""
import logging
import re
import aiohttp
import json

from playwright.async_api import async_playwright, Browser, Page

from src.dto.publish_product_data import PublishProductData
from src.config import settings

logger = logging.getLogger(__name__)


class HoroshopIntegration:
    """Automates product listing on Хорошоп via Playwright."""

    def __init__(self):
        self._playwright = None
        self._browser: Browser | None = None
        self._page: Page | None = None

    async def _ensure_browser(self) -> Page:
        """Launch browser and return page, reusing if already open."""
        if self._page and not self._page.is_closed():
            return self._page

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=settings.playwright_headless)
        self._page = await self._browser.new_page()
        return self._page

    async def publish_product(self, data: PublishProductData) -> None:
        """Full flow: login → create product → fill form → upload photos → save.

        Args:
            data: Combined product input and AI-generated content.
        """
        page = await self._ensure_browser()

        await self._login(page)
        await self._navigate_to_new_product(page)
        await self._fill_product_form(page, data)
        await self._fill_product_specs(page, data)
        await self._fill_seo_fields(page, data)
        await self._upload_photos(page, data)
        await self._save(page)
        await self._add_video(page, data)

        logger.info("Product published on Хорошоп: %s", data.ai_content.title_ua)

    async def _login(self, page: Page) -> None:
        """Log into Хорошоп admin panel."""
        login_url = f"{settings.horoshop_store_url}"
        logger.info("Navigating to Хорошоп admin: %s", login_url)

        await page.goto(login_url)
        await page.fill('input[type="text"]', settings.horoshop_email)
        await page.fill('input[type="password"]', settings.horoshop_password)
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(5000)
        await page.wait_for_load_state("networkidle")

        logger.info("Logged into Хорошоп")

    async def _navigate_to_new_product(self, page: Page) -> None:
        """Navigate to the new product form."""
        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')

        await admin_frame.locator('#addGoodToCatalog').click()
        logger.info("active added")
        add_button = admin_frame.locator('a.button.add:has-text("Додати")')
        await add_button.click()
        await page.wait_for_load_state("networkidle")
        await admin_frame.locator('input[name="modifications[0][article]"]').wait_for(state="visible")

        logger.info("Opened new product form")

    async def _fill_product_form(self, page: Page, data: PublishProductData) -> None:
        """Fill in the main product fields."""
        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        ai = data.ai_content
        input_data = data.input_data

        await admin_frame.locator('input[name="modifications[0][article]"]').fill(input_data.product_code)
        await admin_frame.locator('input[name="modifications[0][i18n][3][mod_title]"]').fill(ai.title_ua)
        await admin_frame.locator('input[name="modifications[0][i18n][4][mod_title]"]').fill(ai.title_en)
        await admin_frame.locator('input[name="modifications[0][price]"]').fill(str(input_data.price))
        await admin_frame.locator('select[name="modifications[0][presence]"]').select_option(value="1")

        presence_select = admin_frame.locator('select[name="modifications[0][presence]"]')
        await presence_select.scroll_into_view_if_needed()

        editor_frame_ua = admin_frame.frame_locator('.cke_wysiwyg_frame').first
        editor_body_ua = editor_frame_ua.locator('body.cke_editable')
        await (editor_body_ua.fill(ai.description_ua))

        editor_frame_en = admin_frame.frame_locator('.cke_wysiwyg_frame').nth(2)
        editor_body_en = editor_frame_en.locator('body.cke_editable')
        await editor_body_en.fill(ai.description_en)

        logger.info("Filled product form fields")

    async def _fill_product_specs(self, page: Page, data: PublishProductData) -> None:
        """Fill in the specs product fields."""
        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        input_data = data.input_data
        ai_data = data.ai_content

        await admin_frame.locator('select[name="names[tipNozha]"]').select_option(label=input_data.blade_type)
        await admin_frame.locator('select[name="names[nazvaNozha]"]').select_option(label=input_data.blade_name)
        await admin_frame.locator('select[name="names[pxvi]"]').select_option(label=input_data.sheath_type)
        if input_data.configuration_type is not None:
            await admin_frame.locator('select[name="names[komplekt]"]').select_option(label=input_data.configuration_type)

        #---- Checkbox ---
        steel_label = admin_frame.locator('label').filter(has_text=input_data.steel)
        await steel_label.locator('input[type="checkbox"]').check()
        if input_data.handle_material is not None:
            handle_label = admin_frame.locator('label').filter(has_text=input_data.handle_material)
            await handle_label.locator('input[type="checkbox"]').check()
        for mount in input_data.attachments:
            await admin_frame.get_by_role("checkbox", name=mount, exact=True).check()
        if input_data.has_lanyard:
            lanyard_label = admin_frame.locator('label').filter(has_text='Темляк')
            await lanyard_label.locator('input[type="checkbox"]').check()
        if input_data.has_flint:
            flint_label = admin_frame.locator('label').filter(has_text='Кресало для розпалу вогнища')
            await flint_label.locator('input[type="checkbox"]').check()
        if input_data.has_honing_rod:
            rod_label = admin_frame.locator('label').filter(has_text='Мусат рубіновий')
            await rod_label.locator('input[type="checkbox"]').check()

        labels_to_check = []

        match input_data.engraving_count:
            case 1:
                labels_to_check = ['Одна сторона']
            case 2:
                labels_to_check = ['Дві сторони']
            case 3:
                labels_to_check = ['Три сторони']
            case 4:
                labels_to_check = ['Одна сторона', 'Три сторони']

        for label_text in labels_to_check:
            await admin_frame.get_by_role("checkbox", name=label_text, exact=True).check()

        for style in ai_data.engraving_style:
            style_label = admin_frame.locator('label').filter(has_text=style)
            await style_label.locator('input[type="checkbox"]').scroll_into_view_if_needed()
            await style_label.locator('input[type="checkbox"]').check()

        # ---------------------------------------------------------------------------------------------------
        await admin_frame.locator('input[name="names[tverdystPoRokvelu]"]').fill(str(input_data.hardness))
        await admin_frame.locator('input[name="names[vagaKlinka]"]').fill(str(input_data.blade_weight))
        await admin_frame.locator('input[name="names[zagalnaDovzhinaMm]"]').fill(str(input_data.total_length))
        await admin_frame.locator('input[name="names[dovzhinaKlinkaMm]"]').fill(str(input_data.blade_length))
        await admin_frame.locator('input[name="names[shirinaKlinkaMm]"]').fill(str(input_data.blade_width))
        await admin_frame.locator('textarea[name="names[i18n][3][tovshinaObuxa]"]').fill(str(input_data.blade_thickness))
        await admin_frame.locator('textarea[name="names[i18n][4][tovshinaObuxa]"]').fill(str(input_data.blade_thickness))
        await admin_frame.locator('input[name="names[kutZatochkiC2b0]"]').fill(str(input_data.sharpening_angle))

        logger.info("Filled product specs fields")

    async def _upload_photos(self, page: Page, data: PublishProductData) -> None:
        """Upload product photos."""
        if not data.input_data.photos:
            logger.info("No photos to upload")
            return

        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        add_button = admin_frame.locator('a:has-text("Додати зображення")').nth(1)
        await add_button.click()

        file_input = admin_frame.locator('input[type="file"]')
        await file_input.set_input_files(data.input_data.photos)

        logger.info("Uploaded %d photos", len(data.input_data.photos))

    async def _fill_seo_fields(self, page: Page, data: PublishProductData) -> None:
        """Fill SEO-related fields."""
        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        ai = data.ai_content

        await admin_frame.locator('input[name="parent_common[i18n][3][seo_title]"]').fill(ai.title_ua)
        await admin_frame.locator('input[name="parent_common[i18n][3][h1_title]"]').fill(ai.title_ua)
        await admin_frame.locator('input[name="parent_common[i18n][4][seo_title]"]').fill(ai.title_en)
        await admin_frame.locator('input[name="parent_common[i18n][4][h1_title]"]').fill(ai.title_en)

        await admin_frame.locator('input[name="parent_common[i18n][3][seo_keywords]"]').fill(ai.meta_keywords_ua)
        await admin_frame.locator('input[name="parent_common[i18n][4][seo_keywords]"]').fill(ai.meta_keywords_en)

        await admin_frame.locator('textarea[name="parent_common[i18n][3][seo_description]"]').fill(ai.meta_description_ua)
        await admin_frame.locator('textarea[name="parent_common[i18n][4][seo_description]"]').fill(ai.meta_description_en)

        logger.info("Filled SEO fields")

    async def _add_additional_categories(self, page: Page) -> None:
        """Selecting suggest categories"""

        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        category_select = admin_frame.locator(
            'select',
            has=admin_frame.get_by_text("[ Розділ ]", exact=True)
        ).first
        add_button = category_select.locator("..").get_by_role("link", name="Додати розділ", exact=True)

        await category_select.select_option(value="1083")
        await page.wait_for_timeout(500)
        await add_button.click()
        await page.wait_for_timeout(500)

        await category_select.select_option(value="1094")
        await add_button.click()

        logger.info("Додаткові розділи успішно додано")

    async def _generate_youtube_iframe(self, url: str) -> str:
        """
        Extracts the video ID from a YouTube URL, fetches the video title,
        and returns a formatted HTML iframe block.
        """
        match = re.search(r"(?:shorts/|v=|youtu\.be/)([0-9A-Za-z_-]{11})", url)
        if not match:
            logger.error(f"Could not extract YouTube ID from URL: {url}")
            return ""

        video_id = match.group(1)

        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        title = "YouTube Video"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(oembed_url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        title = data.get("title", title)
        except Exception as e:
            logger.error(f"Failed to fetch YouTube title for {video_id}: {e}")

        safe_title = title.replace('"', '&quot;')

        iframe_html = (
            f'<iframe width="315" height="560" '
            f'src="https://www.youtube.com/embed/{video_id}" '
            f'title="{safe_title}" '
            f'frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'referrerpolicy="strict-origin-when-cross-origin" '
            f'allowfullscreen></iframe>'
        )

        return iframe_html

    async def _add_video(self, page: Page, data: PublishProductData) -> None:
        """Generates the iframe and injects it into the Horoshop image block."""
        video_url = data.input_data.video_url

        if not video_url:
            logger.info("No video URL provided. Skipping video insertion.")
            return

        logger.info(f"Processing YouTube video: {video_url}")
        video_html = await self._generate_youtube_iframe(video_url)

        if not video_html:
            logger.error("Failed to generate iframe HTML. Skipping video.")
            return

        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        target_photo_block = admin_frame.locator('li.modifications_imagepreview').last

        edit_button = target_photo_block.locator('a[class = "edit make-edit"]')
        await target_photo_block.hover()
        await page.wait_for_timeout(300)
        await edit_button.click(force=True)
        await page.wait_for_timeout(300)

        video_textarea = target_photo_block.locator('textarea[placeholder="код відео"]')
        await video_textarea.fill(video_html)
        await self._save(page)
        await page.wait_for_timeout(5000)

        logger.info("✅ YouTube video iframe successfully injected.")

    async def _save(self, page: Page) -> None:
        """Click the save/publish button."""
        admin_frame = page.frame_locator('iframe[src*="/adminLegacy/data.php"]')
        button_save = admin_frame.get_by_role("link", name="Зберегти", exact=True).first
        await button_save.click()
        await page.wait_for_load_state("networkidle")

        logger.info("Product saved")

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        self._page = None
        self._browser = None
        self._playwright = None
