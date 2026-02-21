"""Orchestrator service that combines Sheets data + Gemini AI into ProductData."""
from src.dto.gemini_content_dto import GeminiContentDto
from src.models.product_data import ProductData
from src.repositories.product_repository import fetch_product_from_sheet
from src.services.gemini_service import GeminiService


class ProductService:
    """Fetches a product by ID, enriches it with AI, returns ProductData."""

    def __init__(self, gemini_service: GeminiService | None = None):
        self.gemini = gemini_service or GeminiService()

    async def get_product(self, product_id: str) -> ProductData:
        """Full pipeline: Sheets → Gemini → ProductData.

        Args:
            product_id: The product identifier used in Google Sheets.

        Returns:
            A fully populated ``ProductData`` instance.
        """
        raw: dict = await fetch_product_from_sheet(product_id)

        photo_links: list[str] = raw.pop("photo_links", [])

        ai_content: GeminiContentDto = await self.gemini.generate_content(
            specs=raw,
            photo_paths=photo_links,
        )

        return ProductData(
            product_code=ai_content.product_code,
            title=ai_content.title,
            description=ai_content.description,
            meta_keywords=ai_content.meta_keywords,
            meta_description=ai_content.meta_description,
            etsy_title=ai_content.etsy_title,
            etsy_description=ai_content.etsy_description,
            etsy_tags=ai_content.etsy_tags,
            photo_links=photo_links,
            price=raw.get("price", ""),
            blade_type=raw.get("blade_type", ""),
            blade_name=raw.get("blade_name", ""),
            steel=raw.get("steel", ""),
            handle_material=raw.get("handle_material", ""),
            sheath_color=raw.get("sheath_color", ""),
            mounts=raw.get("mounts", ""),
            accessories=raw.get("accessories", ""),
            engraving_style=raw.get("engraving_style", ""),
            engravings_on_blade_count=raw.get("engravings_on_blade_count", ""),
            hardness=raw.get("hardness", ""),
            weight=raw.get("weight", ""),
            total_length=raw.get("total_length", ""),
            blade_length=raw.get("blade_length", ""),
            width=raw.get("width", ""),
            thickness=raw.get("thickness", ""),
            etsy_materials=raw.get("etsy_materials", ""),
        )
