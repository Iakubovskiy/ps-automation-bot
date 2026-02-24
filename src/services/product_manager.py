"""Product manager — orchestrates the AI content generation and publish pipeline."""
import logging
from dataclasses import asdict

from src.dto.input_product_data import InputProductData
from src.dto.publish_product_data import PublishProductData
from src.services.ai_service import AiService
from src.services.publish_service import PublishService

logger = logging.getLogger(__name__)


class ProductManager:
    """Orchestrates the product processing pipeline.

    Receives collected product data, sends it through an AI service
    for content generation, and forwards the result to the publish module.
    """

    def __init__(
        self,
        ai_service: AiService,
        publish_service: PublishService | None = None,
    ):
        self.ai_service = ai_service
        self.publish_service = publish_service or PublishService()

    async def process(self, input_data: InputProductData) -> None:
        """Run the full processing pipeline for a single product.

        1. Convert input data to a specs dict for the AI prompt.
        2. Call the AI service to generate marketing content.
        3. Bundle everything into ``PublishProductData``.
        4. Hand off to the publish service.

        Args:
            input_data: Collected product data including photo/video paths.
        """
        logger.info("Processing product: %s", input_data.blade_name)

        specs = asdict(input_data)
        photos = specs.pop("photos", [])
        specs.pop("video_path", None)

        ai_content = await self.ai_service.generate_content(
            specs=specs,
            photo_paths=photos,
        )

        publish_data = PublishProductData(
            input_data=input_data,
            ai_content=ai_content,
        )

        await self.publish_service.publish(publish_data)
