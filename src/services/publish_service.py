"""Publish service — orchestrates publishing across platform integrations."""
import logging

from src.dto.publish_product_data import PublishProductData
from src.services.horoshop_integration import HoroshopIntegration

logger = logging.getLogger(__name__)


class PublishService:
    """Publishes product data to one or more e-commerce platforms."""

    def __init__(
        self,
        horoshop: HoroshopIntegration | None = None,
    ):
        self.horoshop = horoshop or HoroshopIntegration()

    async def publish(self, data: PublishProductData) -> None:
        """Publish product to all configured platforms.

        Each integration runs independently — one failure doesn't block the rest.

        Args:
            data: Combined product input and AI-generated content.
        """
        logger.info("Publishing product: %s", data.input_data.blade_name)

        integrations = {
            "Хорошоп": self.horoshop,
        }

        for name, integration in integrations.items():
            try:
                await integration.publish_product(data)
                logger.info("✅ Published to %s", name)
            except Exception:
                logger.exception("❌ Failed to publish to %s", name)

    async def close(self) -> None:
        """Clean up all integration resources."""
        await self.horoshop.close()
