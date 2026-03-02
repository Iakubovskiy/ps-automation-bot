"""Use case & Celery task: Publish a Product to all active drivers.

Triggered by ProductCreatedEvent via Celery:
  1. Looks up Product and all active DistributionDrivers for its org.
  2. For each driver, find-or-create a manifest.
  3. Instantiate the appropriate driver class (e.g. HoroshopDriver).
  4. Execute publish through Playwright.
"""
import asyncio
import logging

from celery import shared_task
from django.conf import settings

from modules.catalog.domain.product import Product
from modules.distribution.domain.distribution_manifest import DistributionManifest
from modules.distribution.infrastructure.driver_repository import DriverRepository
from modules.distribution.infrastructure.manifest_repository import ManifestRepository
from modules.distribution.infrastructure.playwright_browser import PlaywrightBrowser
from modules.distribution.drivers.horoshop_driver import HoroshopDriver

logger = logging.getLogger(__name__)

# Registry of driver_type → driver class
_DRIVER_REGISTRY: dict[str, type] = {
    "horoshop": HoroshopDriver,
}


class PublishProductUseCase:
    """Publish a product to all active distribution platforms.

    Resolves the driver_type to a concrete driver class,
    and passes the manifest + product data for publishing.
    """

    async def execute(self, product_id: str) -> None:
        """Publish to all active drivers for the product's organization.

        Args:
            product_id: UUID of the Product to publish.
        """
        product = Product.objects.select_related("category").get(pk=product_id)

        drivers = DriverRepository.find_active_by_organization(
            str(product.organization_id)
        )

        if not drivers:
            logger.warning(
                "No active drivers for org %s — skipping publish",
                product.organization_id,
            )
            return

        # Build the product data dict that drivers consume
        product_data = {
            "id": str(product.id),
            "attributes": product.attributes,
            "category": product.category.name,
            "ai_content": product.attributes.get("ai_content", {}),
        }

        headless = getattr(settings, "PLAYWRIGHT_HEADLESS", True)
        browser = PlaywrightBrowser(headless=headless)

        try:
            for driver_config in drivers:
                driver_type = driver_config.driver_type
                driver_cls = _DRIVER_REGISTRY.get(driver_type)

                if not driver_cls:
                    logger.error("Unknown driver_type: %s", driver_type)
                    continue

                # Find or create manifest for this driver + product
                manifest = ManifestRepository.find_or_create(
                    driver_id=str(driver_config.id),
                    product_id=str(product.id),
                    manifest_config=driver_config.credentials.get(
                        "default_manifest", {}
                    ),
                )

                driver = driver_cls(browser)

                logger.info(
                    "Publishing product %s via %s (%s)",
                    product.id,
                    driver_config.name,
                    driver_type,
                )

                try:
                    await driver.publish(manifest, product_data)
                except Exception:
                    logger.exception(
                        "Failed to publish product %s via %s",
                        product.id,
                        driver_config.name,
                    )
        finally:
            await browser.close()


# ── Celery task (entry point from ProductCreatedEvent) ───────────────

@shared_task(
    name="handle_product_created_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def handle_product_created_event(self, event_data: dict) -> None:
    """Celery task triggered by ProductCreatedEvent via EventBus.

    Args:
        event_data: Serialized ProductCreatedEvent dict.
    """
    product_id = event_data.get("product_id")
    if not product_id:
        logger.error("ProductCreatedEvent missing product_id: %s", event_data)
        return

    logger.info("Received ProductCreatedEvent for product %s", product_id)

    use_case = PublishProductUseCase()

    try:
        asyncio.run(use_case.execute(product_id))
    except Exception as exc:
        logger.exception("Publish failed for product %s, retrying…", product_id)
        raise self.retry(exc=exc)
