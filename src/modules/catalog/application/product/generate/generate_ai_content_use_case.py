"""Use case & Celery task: Generate AI content for a Product.

Listens to ProductCreatedEvent, calls Gemini with the ProductSchema's system_prompt
and collected attributes + photos, then stores AI results in Product.attributes
and fires ProductEnrichedEvent to trigger distribution.
"""
import asyncio
import logging
import shutil
import os

from celery import shared_task
from asgiref.sync import sync_to_async

from core.events import EventBus
from modules.catalog.domain.events.product_enriched_event import ProductEnrichedEvent
from modules.catalog.domain.product import Product
from modules.catalog.infrastructure.gemini_service import (
    GeminiService,
    download_photos_for_ai,
)

logger = logging.getLogger(__name__)


def _get_rozetka_instructions(organization_id: str) -> str:
    """Load Rozetka-specific AI instructions if an active Rozetka feed config exists."""
    try:
        from modules.distribution.domain.integrations.rozetka.rozetka_feed_config import RozetkaFeedConfig
        config = RozetkaFeedConfig.objects.filter(
            driver__organization_id=organization_id,
            driver__status="ACTIVE",
        ).first()
        if not config:
            return ""

        parts = []
        if config.rozetka_name_instructions:
            parts.append(config.rozetka_name_instructions)
        if config.rozetka_description_instructions:
            parts.append(config.rozetka_description_instructions)
        return "\n\n".join(parts)
    except Exception:
        logger.debug("Could not load Rozetka instructions", exc_info=True)
        return ""


class GenerateAiContentUseCase:
    """Generate AI content for a product using Gemini.

    Flow:
        1. Load Product with ProductSchema
        2. mark_ai_processing()
        3. Download photos from S3
        4. Call GeminiService with system_prompt + collected attributes + photos
        5. mark_ready(ai_result) — merges AI fields into product.attributes
        6. Publish ProductEnrichedEvent
    """

    def __init__(self, gemini_service: GeminiService | None = None):
        self._gemini = gemini_service or GeminiService()

    async def execute(self, product_id: str) -> None:
        """Run AI content generation for the given product."""
        try:
            product = await Product.objects.select_related("product_schema").aget(pk=product_id)
        except Product.DoesNotExist:
            logger.error("Product %s not found. Aborting AI generation.", product_id)
            return

        product_schema = product.product_schema
        system_prompt = product_schema.system_prompt

        if not system_prompt:
            logger.warning(
                "ProductSchema '%s' has no system_prompt. Skipping AI generation for product %s.",
                product_schema.name,
                product_id,
            )
            EventBus.publish(
                ProductEnrichedEvent(
                    product_id=str(product.id),
                    organization_id=str(product.organization_id),
                )
            )
            return

        # Append Rozetka-specific AI instructions if configured
        rozetka_instructions = await sync_to_async(_get_rozetka_instructions)(
            str(product.organization_id)
        )
        if rozetka_instructions:
            system_prompt = f"{system_prompt}\n\n{rozetka_instructions}"

        await sync_to_async(product.mark_ai_processing)()

        photo_s3_keys = product.attributes.get("photo_s3_keys", [])
        photo_paths: list[str] = []
        temp_dir: str | None = None

        try:
            if photo_s3_keys:
                photo_paths = await download_photos_for_ai(
                    s3_paths=photo_s3_keys,
                    organization_id=str(product.organization_id),
                )
                if photo_paths:
                    temp_dir = os.path.dirname(photo_paths[0])

            # Call Gemini
            ai_result = await self._gemini.generate_content(
                system_prompt=system_prompt,
                collected_attributes=product.attributes,
                photo_paths=photo_paths,
            )

            if not ai_result:
                logger.error("Gemini returned empty result for product %s", product_id)
                await sync_to_async(product.mark_error)()
                return

            await sync_to_async(product.mark_ready)(ai_result)

            logger.info(
                "AI content generated for product %s (%d fields)",
                product_id,
                len(ai_result),
            )

            EventBus.publish(
                ProductEnrichedEvent(
                    product_id=str(product.id),
                    organization_id=str(product.organization_id),
                )
            )

        except Exception:
            logger.exception("AI generation failed for product %s", product_id)
            await sync_to_async(product.mark_error)()

        finally:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


# ── Celery task ──────────────────────────────────────────────────────


@shared_task(
    name="handle_product_created_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def handle_product_created_event(self, event_data: dict) -> None:
    """Listen to ProductCreatedEvent and trigger AI content generation."""
    product_id = event_data.get("product_id")
    if not product_id:
        return

    logger.info("Received ProductCreatedEvent for %s. Starting AI generation...", product_id)

    use_case = GenerateAiContentUseCase()

    try:
        asyncio.run(use_case.execute(product_id))
    except Exception as exc:
        logger.exception("AI generation failed for product %s, retrying…", product_id)
        raise self.retry(exc=exc)
