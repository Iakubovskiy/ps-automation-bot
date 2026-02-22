"""Smoke test for ProductManager with real GeminiService."""
import asyncio
import logging

from src.dto.input_product_data import InputProductData
from src.services.gemini_service import GeminiService
from src.services.product_manager import ProductManager

logging.basicConfig(level=logging.INFO)


async def main():
    mock_input = InputProductData(
        blade_name="Kozak",
        total_length=280,
        blade_length=150,
        blade_width=35,
        blade_weight=180,
        blade_thickness=4,
        hardness=58,
        sharpening_angle=20,
        configuration_type=None,
        blade_type="fixed",
        sheath_type="leather",
        attachments=["MolleLok"],
        has_honing_rod=True,
        has_lanyard=False,
        has_flint=True,
        engraving_count=2,
        handle_type="walnut",
        steel="D2",
        price=1200.0,
        photos=["/app/media/puluj.jpg"],
    )

    manager = ProductManager(ai_service=GeminiService())

    try:
        await manager.process(mock_input)
    except NotImplementedError as e:
        print(f"\n✅ Pipeline works! Stopped at publish stub: {e}")


if __name__ == "__main__":
    asyncio.run(main())
