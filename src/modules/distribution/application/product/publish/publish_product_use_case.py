"""Use case & Celery task: Publish a Product to all active drivers."""
import asyncio
import logging

from django.apps import apps
from celery import shared_task
from django.conf import settings
from asgiref.sync import sync_to_async

from modules.catalog.domain.product import Product
from modules.distribution.infrastructure.driver_repository import DriverRepository
from modules.distribution.infrastructure.task_repository import TaskRepository
from modules.distribution.infrastructure.playwright_browser import PlaywrightBrowser
from modules.distribution.drivers.horoshop.horoshop_driver import HoroshopDriver
from modules.distribution.infrastructure.manifest.facade.manifest_facade import ManifestFacadeRepository
from modules.distribution.domain.integrations.horoshop.enums.event_type import EventType

logger = logging.getLogger(__name__)

_DRIVER_REGISTRY: dict[str, type] = {
    "horoshop": HoroshopDriver,
}


class PublishProductUseCase:
    """Publish a product to all active distribution platforms."""

    @sync_to_async
    def _resolve_labels(self, attributes: dict) -> dict:
        """Перекладає системні ключі (напр. 'Tanto') у людські лейбли ('Танто') з БД."""
        try:
            StaticReference = apps.get_model("catalog", "StaticReference")
            ref_map = dict(StaticReference.objects.values_list("key", "label"))
        except LookupError:
            logger.error("Модель StaticReference не знайдена. Пропускаю переклад лейблів.")
            return attributes

        resolved = dict(attributes)
        for k, v in resolved.items():
            if isinstance(v, str) and v in ref_map:
                resolved[k] = ref_map[v]
            elif isinstance(v, list):
                resolved[k] = [ref_map.get(item, item) if isinstance(item, str) else item for item in v]

        return resolved

    async def execute(self, product_id: str) -> None:
        """Publish to all active drivers for the product's organization."""
        try:
            product = await Product.objects.select_related("category").aget(pk=product_id)
        except Product.DoesNotExist:
            logger.error("Product %s not found. Aborting publish.", product_id)
            return

        drivers = await sync_to_async(DriverRepository.find_active_by_organization)(
            str(product.organization_id)
        )

        if not drivers:
            logger.warning("No active drivers for org %s — skipping publish", product.organization_id)
            return

        resolved_attributes = await self._resolve_labels(product.attributes)

        product_data = {
            "id": str(product.id),
            "attributes": resolved_attributes,
            "category": product.category.name,
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

                manifest_data = await sync_to_async(ManifestFacadeRepository.find_for_driver)(
                    driver_config=driver_config,
                    category_id=str(product.category_id),
                    event_type=EventType.CREATE
                )

                if not manifest_data:
                    logger.warning(
                        "No manifest template found for driver %s and category %s. Skipping.",
                        driver_config.name,
                        product.category.name
                    )
                    continue

                task = await sync_to_async(TaskRepository.find_or_create)(
                    driver_id=str(driver_config.id),
                    product_id=str(product.id)
                )

                logger.info(
                    "Publishing product %s via %s, type: %s",
                    product.id,
                    driver_config.name,
                    driver_type,
                )

                driver_instance = driver_cls(browser)

                try:
                    await driver_instance.publish(
                        task=task,
                        manifest_data=manifest_data,
                        product_data=product_data,
                        organization_id=str(product.organization_id),
                    )
                except Exception as exc:
                    await sync_to_async(task.mark_failed)(str(exc))
                    logger.exception("Failed to publish product %s via %s", product.id, driver_config.name)
        finally:
            await browser.close()

@shared_task(
    name="handle_product_enriched_event",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def handle_product_enriched_event(self, event_data: dict) -> None:
    """Listens to ProductEnrichedEvent and starts distribution."""
    product_id = event_data.get("product_id")
    if not product_id:
        return

    logger.info("Received ProductEnrichedEvent for %s. Starting distribution...", product_id)

    use_case = PublishProductUseCase()

    try:
        asyncio.run(use_case.execute(product_id))
    except Exception as exc:
        logger.exception("Publish failed, retrying...")
        raise self.retry(exc=exc)
