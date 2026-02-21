"""Stub for the publish module."""
import logging

from src.dto.publish_product_data import PublishProductData

logger = logging.getLogger(__name__)


class PublishService:
    """Placeholder for the future publish module."""

    async def publish(self, data: PublishProductData) -> None:
        """Publish product data to external platforms.

        Args:
            data: Combined product input and AI-generated content.

        Raises:
            NotImplementedError: Always — to be implemented later.
        """
        logger.info("PublishService.publish called for blade: %s", data.input_data.blade_name)
        raise NotImplementedError("Publish module is not implemented yet.")
