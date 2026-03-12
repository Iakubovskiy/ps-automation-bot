import os
import time
import logging
import re
import tempfile
import aiohttp
from typing import Any
from asgiref.sync import sync_to_async

from playwright.async_api import Page
from modules.distribution.infrastructure.playwright_browser import PlaywrightBrowser
from modules.distribution.domain.distribution_task import DistributionTask
from modules.distribution.domain.integrations.horoshop.horoshop_step import HoroshopStep
from modules.distribution.domain.integrations.horoshop.enums.action_type import ActionType
from modules.catalog.infrastructure.s3_service import S3Service
from modules.users.domain.organization import Organization

logger = logging.getLogger(__name__)

class HoroshopDriver:
    """Driver for publishing products to Horoshop via Playwright."""

    def __init__(self, browser: PlaywrightBrowser):
        self._browser = browser
        self._temp_dirs: list[tempfile.TemporaryDirectory] = []

    def _resolve_path(self, context: dict, path: str) -> Any:
        """Resolve a dot-separated path in a dictionary."""
        keys = path.split(".")
        val = context
        for key in keys:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                return None
        return val

    async def _download_s3_photos(self, s3_paths: list[str], organization_id: str) -> list[str]:
        """Download S3 photos to a local temp folder for Playwright upload."""
        if not s3_paths:
            return []

        org = await Organization.objects.aget(id=organization_id)
        s3_service = S3Service(org=org)

        base_dir = "/app/media/temp_publish"
        os.makedirs(base_dir, exist_ok=True)

        temp_dir = tempfile.TemporaryDirectory(dir=base_dir, prefix="pub_")
        self._temp_dirs.append(temp_dir)

        local_paths = []
        for s3_path in s3_paths:
            if not s3_path:
                continue
            file_name = os.path.basename(s3_path)
            local_path = os.path.join(temp_dir.name, file_name)
            await sync_to_async(s3_service.download_file)(s3_path, local_path)
            local_paths.append(local_path)

        logger.info("Downloaded %d photos to %s", len(local_paths), temp_dir.name)
        return local_paths

    async def _generate_youtube_iframe(self, url: str) -> str:
        """Converts a YouTube URL to an iframe format."""
        match = re.search(r"(?:shorts/|v=|youtu\.be/)([0-9A-Za-z_-]{11})", url)
        if not match:
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
        except Exception:
            pass

        safe_title = title.replace('"', '&quot;')
        return (
            f'<iframe width="315" height="560" '
            f'src="https://www.youtube.com/embed/{video_id}" '
            f'title="{safe_title}" '
            f'frameborder="0" '
            f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            f'referrerpolicy="strict-origin-when-cross-origin" '
            f'allowfullscreen></iframe>'
        )

    async def _execute_step(self, page: Page, step: HoroshopStep, context: dict) -> None:
        try:
            action = ActionType(step.action)
        except ValueError:
            logger.warning("Unknown action: %s", step.action)
            return

        value = None
        if step.value_source:
            value = self._resolve_path(context, step.value_source)
        if value is None and step.static_value:
            value = step.static_value

        base = page
        if step.iframe_selector:
            for frame_sel in step.iframe_selector.split("|"):
                base = base.frame_locator(frame_sel.strip()).first

        clean_selector = step.selector.replace('\\"', '"') if step.selector else None
        target = base.locator(clean_selector) if clean_selector else None

        match action:
            case ActionType.GOTO:
                url = self._resolve_path(context, step.url_source) if step.url_source else step.static_url
                if url:
                    await page.goto(str(url))

            case ActionType.CLICK:
                if target:
                    if step.force_click:
                        await target.dispatch_event("click")
                    else:
                        await target.click()

            case ActionType.HOVER:
                if target:
                    await target.hover()

            case ActionType.FILL:
                if target and value is not None:
                    await target.fill(str(value))

            case ActionType.FILL_IFRAME:
                if target and value is not None:
                    await target.fill(str(value))

            case ActionType.FILL_YOUTUBE_IFRAME:
                if target and value:
                    iframe_html = await self._generate_youtube_iframe(str(value))
                    if iframe_html:
                        await target.fill(iframe_html)

            case ActionType.SELECT:
                if target and value is not None:
                    str_val = str(value)
                    logger.info("Trying to select option: '%s' in %s", str_val, clean_selector)
                    try:
                        await target.select_option(value=str_val)
                    except Exception:
                        await target.select_option(label=str_val)

            case ActionType.CHECK:
                items = value if isinstance(value, list) else [value] if value else []
                if items and not target:
                    for item in items:
                        exact_match_pattern = re.compile(rf"^\s*{re.escape(str(item))}\s*$")
                        label = base.locator("label").filter(has_text=exact_match_pattern)
                        await label.locator('input[type="checkbox"]').check()
                elif value and target:
                    await target.check()

            case ActionType.UPLOAD:
                logger.info("UPLOAD action: target=%s, value=%s", bool(target), value)
                if target and value:
                    s3_paths = value if isinstance(value, list) else [value]
                    try:
                        local_photos = await self._download_s3_photos(
                            s3_paths, context.get("organization_id", "")
                        )
                        logger.info("Downloaded photos: %s", local_photos)
                        if local_photos:
                            await target.set_input_files(local_photos)
                            logger.info("Uploaded %d photos via Playwright", len(local_photos))
                        else:
                            logger.warning("No local photos after S3 download")
                    except Exception as e:
                        logger.exception("UPLOAD failed: %s", e)

            case ActionType.WAIT_NETWORKIDLE:
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    logger.warning("wait_networkidle timeout exceeded, continuing execution...")

            case ActionType.WAIT_TIMEOUT:
                ms = step.timeout_ms or 1000
                await page.wait_for_timeout(ms)

    async def publish(
        self,
        task: DistributionTask,
        manifest_data: list[HoroshopStep],
        product_data: dict,
        organization_id: str,
    ) -> None:
        """Execute the publishing flow defined by manifest steps."""
        if not manifest_data:
            raise ValueError("Manifest contains no steps.")

        credentials = await sync_to_async(lambda: task.driver.credentials)()

        context = {
            "credentials": credentials,
            "product": product_data,
            "organization_id": organization_id,
        }

        page = await self._browser.get_page()

        debug_dir = "/app/media/debug_screenshots"
        os.makedirs(debug_dir, exist_ok=True)

        try:
            for index, step in enumerate(manifest_data):
                logger.info(
                    "Executing step %d/%d: %s selector: %s value: %s", 
                    index + 1, len(manifest_data), 
                    step.action, step.selector, 
                    self._resolve_path(context, step.value_source)
                )
                try:
                    step_screenshot = os.path.join(debug_dir, f"step_{index + 1}_{step.action}.png")
                    await page.screenshot(path=step_screenshot, full_page=True)
                except Exception:
                    pass

                await self._execute_step(page, step, context)

            await sync_to_async(task.mark_published)()
            logger.info("Published product %s", task.product_id)

        except Exception as exc:
            timestamp = int(time.time())
            screenshot_path = os.path.join(debug_dir, f"error_step_{index + 1}_{timestamp}.png")

            try:
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.error("Error screenshot saved at: %s", screenshot_path)
            except Exception as ss_exc:
                logger.error("Failed to capture screenshot: %s", ss_exc)

            step_action = step.action if 'step' in locals() else "Unknown"
            logger.exception("Failed at step %d %s Error: %s", index + 1, step_action, exc)
            raise
        finally:
            for temp_dir in self._temp_dirs:
                try:
                    temp_dir.cleanup()
                except Exception:
                    pass
            self._temp_dirs.clear()
            await page.close()
