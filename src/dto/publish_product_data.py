"""DTO for product data ready to be published."""
from dataclasses import dataclass

from src.dto.gemini_content_dto import GeminiContentDto
from src.dto.input_product_data import InputProductData


@dataclass
class PublishProductData:
    """Combined product data ready for the publish module.

    Bundles the original input specs with AI-generated marketing content.
    """

    input_data: InputProductData
    ai_content: GeminiContentDto
